import AppKit
import SteckwerkCore
import SwiftUI

/// KI: Assistent (Werte aus einer Beschreibung) und „Motiv zeichnen“ mit Ollama, OpenRouter oder ChatGPT.
struct KIView: View {
    @Environment(AppModel.self) private var model

    // Assistent
    @State private var frage = ""
    @State private var assistentAn = false
    @State private var assistentURL = ""
    @State private var assistentModell = ""
    @State private var assistentStatus: String?

    // Bilder
    @State private var quelle = "ollama"
    @State private var stil = "silhouette"
    @State private var beschreibung = ""
    @State private var bildModell = ""
    @State private var key = ""
    @State private var limit: Double = 0
    @State private var bild: NSImage?
    @State private var bildDaten: Data?
    @State private var bildTyp = ""
    @State private var schwelle: Double = 0.5
    @State private var motivName = ""
    @State private var arbeitet = false
    @State private var info: String?

    private var bilderSettings: JSONValue? { model.schema?.assistent?["bilder"] }

    private var stile: [(String, String)] {
        let s = (bilderSettings?["stile"]?.arrayValue ?? []).compactMap { v -> (String, String)? in
            guard let k = v["value"]?.stringValue else { return nil }
            return (k, v["label"]?.stringValue ?? k)
        }
        return s.isEmpty ? [("silhouette", "Silhouette"), ("scherenschnitt", "Scherenschnitt"), ("linien", "Strichzeichnung")] : s
    }

    var body: some View {
        Form {
            Section("Assistent") {
                Toggle("Assistent verwenden (Ollama)", isOn: $assistentAn)
                TextField("Ollama-Adresse", text: $assistentURL)
                TextField("Sprachmodell", text: $assistentModell)
                HStack {
                    Button("Speichern") { Task { await saveAssistent() } }
                    Button("Verbindung prüfen") { Task { await checkAssistent() } }
                    if let s = assistentStatus { Text(s).font(.caption).foregroundStyle(.secondary) }
                }
                if let m = model.selectedModel {
                    TextField("Was soll „\(m.label)“ werden?", text: $frage, axis: .vertical)
                        .lineLimit(2...4)
                    Button("Werte vorschlagen") { Task { await askAssistent() } }
                        .disabled(frage.trimmingCharacters(in: .whitespaces).isEmpty || arbeitet)
                } else {
                    Text("Wähle links ein Modell, dann schlägt der Assistent Werte dafür vor.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }

            Section("Motiv zeichnen") {
                Picker("Anbieter", selection: $quelle) {
                    Text("Ollama (lokal, kostenlos)").tag("ollama")
                    Text("OpenRouter").tag("openrouter")
                    Text("ChatGPT (OpenAI)").tag("chatgpt")
                }
                Picker("Stil", selection: $stil) {
                    ForEach(stile.indices, id: \.self) { i in Text(stile[i].1).tag(stile[i].0) }
                }
                TextField("Bildmodell (leer = Standard)", text: $bildModell)
                if quelle != "ollama" {
                    SecureField(quelle == "chatgpt" ? "OpenAI-Schlüssel" : "OpenRouter-Schlüssel", text: $key,
                                prompt: Text(keyGesetzt ? "gespeichert – leer lassen" : "sk-…"))
                    TextField("Monatslimit (USD, 0 = keins)", value: $limit, format: .number)
                    if let m = bilderSettings?["monat"] {
                        Text(String(format: "Diesen Monat: %d Bilder, %.2f $", Int(m["bilder"]?.doubleValue ?? 0),
                                    m["kosten"]?.doubleValue ?? 0))
                            .font(.caption).foregroundStyle(.secondary)
                    }
                }
                Button("Anbieter speichern") { Task { await saveBild() } }
                TextField("Beschreibung, z. B. „Eule auf einem Ast“", text: $beschreibung, axis: .vertical)
                    .lineLimit(2...4)
                HStack {
                    Button("Zeichnen") { Task { await zeichnen() } }
                        .buttonStyle(.borderedProminent)
                        .disabled(beschreibung.trimmingCharacters(in: .whitespaces).isEmpty || arbeitet)
                    if arbeitet { ProgressView().controlSize(.small) }
                    if let info { Text(info).font(.caption).foregroundStyle(.secondary) }
                }
            }

            if let img = bild {
                Section("Ergebnis") {
                    let istSVG = bildTyp == "image/svg+xml"
                    Image(nsImage: istSVG ? img : (ImageTools.threshold(img, schwelle) ?? img))
                        .resizable()
                        .interpolation(.none)
                        .scaledToFit()
                        .frame(maxHeight: 260)
                        .frame(maxWidth: .infinity)
                    if !istSVG {
                        Slider(value: $schwelle, in: 0.1...0.9) { Text("Schwelle") }
                    }
                    TextField("Name des Motivs", text: $motivName)
                    Button("Als Motiv übernehmen") { Task { await importMotiv() } }
                        .disabled(motivName.trimmingCharacters(in: .whitespaces).isEmpty || arbeitet)
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("KI")
        .onAppear(perform: load)
    }

    private var keyGesetzt: Bool {
        let field = quelle == "chatgpt" ? "chatgpt_key_gesetzt" : "key_gesetzt"
        return bilderSettings?[field]?.boolValue ?? false
    }

    private func load() {
        let a = model.schema?.assistent
        assistentAn = a?["an"]?.boolValue ?? false
        assistentURL = a?["url"]?.stringValue ?? "http://127.0.0.1:11434"
        assistentModell = a?["modell"]?.stringValue ?? ""
        let b = bilderSettings
        quelle = b?["quelle"]?.stringValue ?? "ollama"
        limit = b?["limit"]?.doubleValue ?? 0
    }

    private func run(_ work: @escaping (Bridge) async throws -> Void) async {
        guard let b = model.bridge else { return }
        arbeitet = true
        defer { arbeitet = false }
        do { try await work(b) } catch { model.errorText = error.localizedDescription }
    }

    private func saveAssistent() async {
        await run { b in
            try await b.call("/api/assistent-einstellungen", ["an": .bool(assistentAn), "url": .string(assistentURL),
                                                              "modell": .string(assistentModell)])
            try await model.reloadSchema()
            assistentStatus = "Gespeichert"
        }
    }

    private func checkAssistent() async {
        await run { b in
            let r = try await b.call("/api/assistent-status", ["url": .string(assistentURL)], timeout: 15)
            let n = r["modelle"]?.arrayValue?.count ?? 0
            assistentStatus = (r["vorhanden"]?.boolValue == true ? "erreichbar, Modell da" : "erreichbar, Modell fehlt")
                + " · \(n) Modelle"
        }
    }

    private func askAssistent() async {
        guard let k = model.selectedModelKey, let m = model.selectedModel else { return }
        await run { b in
            let r = try await b.call("/api/assistent", ["model": .string(k), "beschreibung": .string(frage),
                                                        "params": .object(model.values[k] ?? [:])], timeout: 300)
            let werte = r["werte"]?.objectValue ?? [:]
            for p in m.params { if let v = werte[p.key] { model.values[k, default: [:]][p.key] = p.clamp(v) } }
            model.message = r["hinweis"]?.stringValue ?? "\(werte.count) Werte übernommen"
            model.scheduleBuild(delay: 0)
        }
    }

    private func saveBild() async {
        await run { b in
            var body: [String: JSONValue] = ["quelle": .string(quelle), "limit": .number(limit)]
            if !bildModell.isEmpty {
                let feld = ["ollama": "ollama_modell", "openrouter": "openrouter_modell", "chatgpt": "chatgpt_modell"][quelle]
                if let feld { body[feld] = .string(bildModell) }
            }
            if !key.isEmpty { body[quelle == "chatgpt" ? "chatgpt_key" : "key"] = .string(key) }
            try await b.call("/api/bild-einstellungen", body)
            key = ""
            try await model.reloadSchema()
            info = "Gespeichert"
        }
    }

    private func zeichnen() async {
        await run { b in
            var body: [String: JSONValue] = ["beschreibung": .string(beschreibung), "stil": .string(stil),
                                             "quelle": .string(quelle)]
            if !bildModell.isEmpty { body["modell"] = .string(bildModell) }
            let r = try await b.call("/api/bild", body, timeout: 330)
            guard let b64 = r["bild"]?.stringValue, let data = Data(base64Encoded: b64) else {
                throw BridgeError("Kein Bild erhalten")
            }
            bildDaten = data
            bildTyp = r["typ"]?.stringValue ?? ""
            bild = NSImage(data: data)
            if motivName.isEmpty { motivName = String(beschreibung.prefix(30)) }
            let kosten = r["kosten"]?.doubleValue ?? 0
            info = kosten > 0 ? String(format: "Kosten: %.3f $", kosten) : "Fertig"
        }
    }

    private func importMotiv() async {
        guard let data = bildDaten else { return }
        await run { b in
            let isSVG = bildTyp == "image/svg+xml"
            let payload: Data
            if isSVG {
                payload = data
            } else if let img = bild, let bw = ImageTools.threshold(img, schwelle), let png = ImageTools.png(bw) {
                payload = png
            } else {
                throw BridgeError("Bild ließ sich nicht umwandeln")
            }
            let r = try await b.call("/api/motiv-import", [
                "name": .string(motivName), "filename": .string(isSVG ? "motiv.svg" : "motiv.png"),
                "data": .string(payload.base64EncodedString()), "invert": false], timeout: 120)
            model.message = r["message"]?.stringValue
            try await model.reloadSchema()
            info = "Motiv übernommen"
        }
    }
}

enum ImageTools {
    /// Schwarz-weiß mit Schwelle (0…1) – wie die Weboberfläche vor dem Import.
    static func threshold(_ image: NSImage, _ t: Double) -> NSImage? {
        guard let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { return nil }
        let w = cg.width, h = cg.height
        guard w > 0, h > 0, let ctx = CGContext(data: nil, width: w, height: h, bitsPerComponent: 8, bytesPerRow: w,
                                                space: CGColorSpaceCreateDeviceGray(),
                                                bitmapInfo: CGImageAlphaInfo.none.rawValue) else { return nil }
        ctx.setFillColor(gray: 1, alpha: 1)
        ctx.fill(CGRect(x: 0, y: 0, width: w, height: h))
        ctx.draw(cg, in: CGRect(x: 0, y: 0, width: w, height: h))
        guard let buf = ctx.data?.bindMemory(to: UInt8.self, capacity: w * h) else { return nil }
        let limit = UInt8(max(0, min(255, t * 255)))
        for i in 0..<(w * h) { buf[i] = buf[i] < limit ? 0 : 255 }
        guard let out = ctx.makeImage() else { return nil }
        return NSImage(cgImage: out, size: NSSize(width: w, height: h))
    }

    static func png(_ image: NSImage) -> Data? {
        guard let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { return nil }
        return NSBitmapImageRep(cgImage: cg).representation(using: .png, properties: [:])
    }
}
