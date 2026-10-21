import AppKit
import SteckwerkCore
import SwiftUI

/// Versionen und Update-Check: Steckwerk Desktop ersetzt sich selbst aus dem Update-Kanal,
/// Pakete aktualisiert die Seite „Pakete“.
struct AppUpdateView: View {
    @Environment(AppModel.self) private var model
    @State private var check: JSONValue?
    @State private var loading = false

    var body: some View {
        Form {
            Section("Versionen") {
                LabeledContent("Steckwerk Desktop", value: model.appVersion)
                if case .laeuft(_, let v, let eigen) = model.engineState {
                    LabeledContent("Engine", value: v + (eigen ? "" : " (mitbenutzt)"))
                } else {
                    LabeledContent("Engine", value: model.engineState.label)
                }
            }
            DesktopUpdateSection()
            Section("Engine und Pakete") {
                HStack {
                    Button("Nach Updates suchen") { Task { await run() } }
                    if loading { ProgressView().controlSize(.small) }
                }
                if let p = check?["programm"] {
                    if p["neu"]?.boolValue == true {
                        Text("Neue Engine-Version \(p["version"]?.stringValue ?? "") vom \(p["datum"]?.stringValue ?? "")")
                            .font(.headline)
                        ForEach((p["hinweise"]?.arrayValue ?? []).compactMap(\.stringValue), id: \.self) { h in
                            Label(h, systemImage: "sparkle").font(.callout)
                        }
                        if let s = p["seite"]?.stringValue, let url = URL(string: s), !s.isEmpty {
                            Link("Zur Download-Seite", destination: url)
                        }
                    } else {
                        Label("Steckwerk \(p["installiert"]?.stringValue ?? "") ist aktuell", systemImage: "checkmark.circle")
                            .foregroundStyle(Theme.ok)
                    }
                    let n = check?["updates"]?.doubleValue ?? 0
                    if n > 0 {
                        Text("Für \(Int(n)) Paket(e) gibt es Updates – siehe „Pakete“.")
                            .font(.callout).foregroundStyle(.secondary)
                    }
                }
                if let k = check?["kanal"]?.stringValue {
                    Text(k).font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Updates")
    }

    private func run() async {
        guard let b = model.bridge else { return }
        loading = true
        defer { loading = false }
        do {
            check = try await b.call("/api/update-check", timeout: 60)
        } catch {
            model.errorText = error.localizedDescription
        }
    }
}

/// Selbst-Update der nativen App: prüfen, laden, ersetzen, neu starten.
struct DesktopUpdateSection: View {
    @Environment(AppModel.self) private var model
    @State private var info: JSONValue?
    @State private var loading = false
    @State private var installing = false

    var body: some View {
        Section("Steckwerk Desktop") {
            HStack {
                Button("Nach App-Update suchen") { Task { await check() } }
                if loading { ProgressView().controlSize(.small) }
            }
            if case .laeuft(_, _, false) = model.engineState {
                Text("Die App nutzt gerade die Engine der Browser-App mit. Für App-Updates einmal "
                     + "„Modell → Engine neu starten“ wählen, nachdem die Browser-App beendet ist.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            if let d = info {
                if d["neu"]?.boolValue == true {
                    Text("Neue Version \(d["version"]?.stringValue ?? "") vom \(d["datum"]?.stringValue ?? "")")
                        .font(.headline)
                    ForEach((d["hinweise"]?.arrayValue ?? []).compactMap(\.stringValue), id: \.self) { h in
                        Label(h, systemImage: "sparkle").font(.callout)
                    }
                    if d["kann_installieren"]?.boolValue == true {
                        Button {
                            Task { await install() }
                        } label: {
                            Label(installing ? "Wird installiert …" : "Installieren und neu starten",
                                  systemImage: "arrow.down.circle.fill")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(installing)
                    } else if let g = d["grund"]?.stringValue, !g.isEmpty {
                        Text(g).font(.caption).foregroundStyle(Theme.warnung)
                    }
                } else {
                    Label("Steckwerk Desktop \(d["installiert"]?.stringValue ?? model.appVersion) ist aktuell",
                          systemImage: "checkmark.circle")
                        .foregroundStyle(Theme.ok)
                }
            }
        }
        .task { if info == nil { await check() } }
    }

    private func check() async {
        guard let b = model.bridge else { return }
        loading = true
        defer { loading = false }
        do {
            info = try await b.call("/api/desktop-check", timeout: 60)
        } catch {
            info = nil
            if case .laeuft(_, _, true) = model.engineState { model.errorText = error.localizedDescription }
        }
    }

    private func install() async {
        guard let b = model.bridge else { return }
        installing = true
        defer { installing = false }
        do {
            let r = try await b.call("/api/desktop-install", timeout: 600)
            let ziel = r["ziel"]?.stringValue ?? Bundle.main.bundlePath
            try Engine.relaunch(ziel)
            model.shutdown()
            NSApp.terminate(nil)
        } catch {
            model.errorText = "App-Update fehlgeschlagen: \(error.localizedDescription)"
        }
    }
}
