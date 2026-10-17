import AppKit
import SteckwerkCore
import SwiftUI

/// Versionen und Update-Check. Programm-Updates installiert die native App (noch) nicht selbst –
/// sie zeigt, was es Neues gibt, und verlinkt die Seite.
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
            Section("Update-Kanal") {
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
