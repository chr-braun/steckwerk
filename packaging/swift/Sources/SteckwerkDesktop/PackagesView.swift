import AppKit
import SteckwerkCore
import SwiftUI
import UniformTypeIdentifiers

/// Pakete: Kanal-Liste mit Installieren/Aktualisieren, installierte Pakete, lokale .swpaket-Datei.
struct PackagesView: View {
    @Environment(AppModel.self) private var model
    @State private var feed: JSONValue?
    @State private var loading = false

    private var kanal: [[String: JSONValue]] {
        (feed?["pakete"]?.arrayValue ?? []).compactMap(\.objectValue)
    }

    var body: some View {
        Form {
            Section {
                HStack {
                    Button("Kanal prüfen") { Task { await check() } }
                    Button("Alle aktualisieren") { Task { await install(["alle": true]) } }
                        .disabled(feed == nil)
                    Spacer()
                    Button("Paketdatei installieren …") { pickFile() }
                    if loading { ProgressView().controlSize(.small) }
                }
                if let msg = model.message { Text(msg).font(.callout).foregroundStyle(.secondary) }
            }
            Section("Im Kanal") {
                if feed == nil {
                    Text("Noch nicht geprüft").foregroundStyle(.secondary)
                } else if kanal.isEmpty {
                    Text("Der Kanal enthält keine Pakete").foregroundStyle(.secondary)
                }
                ForEach(kanal.indices, id: \.self) { i in
                    let p = kanal[i]
                    let status = p["status"]?.stringValue ?? ""
                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("\(p["name"]?.stringValue ?? "") \(p["version"]?.stringValue ?? "")").font(.headline)
                            Text(p["beschreibung"]?.stringValue ?? "").font(.callout).foregroundStyle(.secondary)
                        }
                        Spacer()
                        switch status {
                        case "neu":
                            Button("Installieren") { Task { await install(["id": p["id"] ?? .null]) } }
                        case "update":
                            Button("Aktualisieren") { Task { await install(["id": p["id"] ?? .null]) } }
                                .buttonStyle(.borderedProminent)
                        case "zu_neu":
                            Text("braucht Steckwerk \(p["steckwerk"]?.stringValue ?? "")")
                                .font(.caption).foregroundStyle(.secondary)
                        default:
                            Label("aktuell", systemImage: "checkmark").foregroundStyle(Theme.ok)
                        }
                    }
                }
            }
            Section("Installiert") {
                let installed = model.schema?.pakete ?? []
                if installed.isEmpty { Text("Keine Pakete installiert").foregroundStyle(.secondary) }
                ForEach(installed) { p in
                    HStack {
                        VStack(alignment: .leading) {
                            Text("\(p.name) \(p.version)")
                            if let f = p.fehler, !f.isEmpty {
                                Text(f).font(.caption).foregroundStyle(Theme.fehler)
                            } else {
                                Text(p.modelle.joined(separator: ", ")).font(.caption).foregroundStyle(.secondary)
                            }
                        }
                        Spacer()
                        Button("Entfernen", role: .destructive) { Task { await remove(p.id) } }
                    }
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Pakete")
        .task { if feed == nil { await check() } }
    }

    private func check() async {
        guard let b = model.bridge else { return }
        loading = true
        defer { loading = false }
        do {
            feed = try await b.call("/api/update-check", timeout: 60)
        } catch {
            model.errorText = error.localizedDescription
        }
    }

    private func install(_ body: [String: JSONValue]) async {
        guard let b = model.bridge else { return }
        loading = true
        defer { loading = false }
        do {
            let r = try await b.call("/api/update-paket", body, timeout: 300)
            model.message = r["message"]?.stringValue
            try await model.reloadSchema()
            await check()
        } catch {
            model.errorText = error.localizedDescription
        }
    }

    private func remove(_ id: String) async {
        guard let b = model.bridge else { return }
        do {
            let r = try await b.call("/api/paket-entfernen", ["id": .string(id)])
            model.message = r["message"]?.stringValue
            try await model.reloadSchema()
        } catch {
            model.errorText = error.localizedDescription
        }
    }

    private func pickFile() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = ["swpaket", "lfpaket", "zip"].compactMap { UTType(filenameExtension: $0) }
        panel.allowsOtherFileTypes = true
        panel.message = "Steckwerk-Paket (.swpaket) wählen"
        guard panel.runModal() == .OK, let url = panel.url else { return }
        Task {
            guard let b = model.bridge else { return }
            do {
                let data = try Data(contentsOf: url)
                let r = try await b.call("/api/paket-installieren", ["data": .string(data.base64EncodedString())],
                                         timeout: 120)
                model.message = r["message"]?.stringValue
                try await model.reloadSchema()
            } catch {
                model.errorText = error.localizedDescription
            }
        }
    }
}
