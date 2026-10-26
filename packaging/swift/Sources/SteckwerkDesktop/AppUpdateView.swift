import SteckwerkCore
import SwiftUI

/// Versionen und Updates: die App selbst und Pakete aus dem Steckwerk-Kanal.
@MainActor
struct AppUpdateView: View {
    @EnvironmentObject var model: AppModel
    @AppStorage(AppModel.autoUpdateKey) var beimStart = true
    @State var busy = false
    @State var installing = false
    @State var message: String?

    var body: some View {
        Form {
            Section("Version") {
                LabeledContent("Steckwerk Desktop", value: AppModel.appVersion)
                LabeledContent("Engine", value: model.engineVersion ?? "–")
            }

            Section {
                HStack {
                    Button {
                        Task { await runCheck() }
                    } label: {
                        Label("Nach Updates suchen", systemImage: "arrow.down.circle")
                    }
                    .disabled(busy)
                    if busy { ProgressView().controlSize(.small) }
                }
                Toggle("Beim Start nach Updates suchen", isOn: $beimStart)

                if let app = model.desktopCheck {
                    programm(app)
                }
                if let check = model.updateCheck {
                    pakete(check)
                }
                if let message {
                    Text(message).textSelection(.enabled)
                }
            } header: {
                Text("Updates")
            } footer: {
                Text("Fragt den Steckwerk-Update-Kanal im Internet ab. Jede Datei wird vor dem Installieren über ihre Prüfsumme geprüft.")
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Updates")
    }

    @ViewBuilder
    private func programm(_ p: DesktopCheck) -> some View {
        if p.neu {
            VStack(alignment: .leading, spacing: 6) {
                Label("Steckwerk Desktop \(p.version) ist verfügbar (installiert: \(p.installiert))", systemImage: "sparkles")
                    .foregroundStyle(Theme.accent)
                    .font(.headline)
                ForEach(Array(p.hinweise.enumerated()), id: \.offset) { _, hinweis in
                    Text("• " + hinweis).font(.callout)
                }
                if p.kannInstallieren {
                    HStack {
                        Button {
                            Task { await installApp() }
                        } label: {
                            Label("Installieren und neu starten", systemImage: "arrow.triangle.2.circlepath")
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(busy)
                        if installing {
                            ProgressView().controlSize(.small)
                            Text("Wird geladen und geprüft …").font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    .padding(.top, 4)
                } else {
                    Text(p.grund.isEmpty ? "Bitte die neue App laden und ersetzen." : p.grund)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        } else {
            Label("Steckwerk Desktop \(p.installiert.isEmpty ? AppModel.appVersion : p.installiert) ist aktuell",
                  systemImage: "checkmark.circle")
                .foregroundStyle(Theme.ok)
        }
    }

    @ViewBuilder
    private func pakete(_ check: UpdateCheck) -> some View {
        let paketUpdates = check.pakete.filter { $0.installiert != nil && $0.installable }
        if paketUpdates.isEmpty {
            Text("Alle installierten Pakete sind aktuell.")
                .foregroundStyle(.secondary)
        } else {
            Text("Paket-Updates: " + paketUpdates.map { "\($0.name) \($0.version)" }.joined(separator: ", "))
            Button("Alle Pakete aktualisieren") {
                Task { await updatePakete() }
            }
            .disabled(busy)
        }
    }

    private func runCheck() async {
        busy = true
        message = nil
        defer { busy = false }
        await model.checkForUpdates()
    }

    private func installApp() async {
        busy = true
        installing = true
        message = nil
        defer {
            busy = false
            installing = false
        }
        do {
            message = try await model.installDesktopUpdate()
        } catch {
            message = error.localizedDescription
        }
    }

    private func updatePakete() async {
        guard let client = model.client else { return }
        busy = true
        defer { busy = false }
        do {
            let response = try await client.alleKanalPaketeInstallieren()
            if let schema = response.schema { model.apply(schema: schema) }
            message = response.message
            await model.checkForUpdates(quiet: true)
        } catch {
            message = error.localizedDescription
        }
    }
}
