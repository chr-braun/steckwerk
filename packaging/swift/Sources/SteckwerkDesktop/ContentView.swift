import SteckwerkCore
import SwiftUI

@MainActor
struct ContentView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        Group {
            switch model.engineState {
            case .running:
                MainSplitView()
            case .starting:
                StartingView()
            case .failed:
                EngineFailureView()
            }
        }
        .background(Theme.background)
        .alert(item: $model.alert) { alert in
            Alert(title: Text(alert.title), message: Text(alert.message), dismissButton: .default(Text("OK")))
        }
    }
}

@MainActor
private struct StartingView: View {
    var body: some View {
        VStack(spacing: 16) {
            ProgressView()
            Text("Engine wird gestartet …")
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

@MainActor
private struct EngineFailureView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Engine startet nicht", systemImage: "exclamationmark.triangle.fill")
                .font(.title2.bold())
                .foregroundStyle(Theme.error)
            Text(model.engineError ?? "Unbekannter Fehler")
                .textSelection(.enabled)
            if !model.engineDetails.isEmpty {
                DisclosureGroup("Details") {
                    ScrollView {
                        Text(model.engineDetails)
                            .font(.system(.caption, design: .monospaced))
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .frame(maxHeight: 240)
                }
            }
            Button("Erneut versuchen") {
                model.restartEngine()
            }
            .keyboardShortcut(.defaultAction)
        }
        .padding(32)
        .frame(maxWidth: 640)
        .card()
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

@MainActor
private struct MainSplitView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        NavigationSplitView {
            SidebarView()
                .navigationSplitViewColumnWidth(min: 200, ideal: 236, max: 320)
        } detail: {
            DetailView()
        }
    }
}

@MainActor
private struct SidebarView: View {
    @EnvironmentObject var model: AppModel

    private var projektTreffer: [Projekt] {
        let q = model.suche.trimmingCharacters(in: .whitespaces).lowercased()
        return q.isEmpty ? Array(model.projekte.prefix(3)) : []
    }

    /// Was in der Liste markiert ist: Einstellungen für beide Reiter, bei einer offenen Vorlage nichts.
    private var markiert: Binding<SidebarItem?> {
        Binding(
            get: {
                switch model.selection {
                case .updates: return .material
                case .model: return nil
                default: return model.selection
                }
            },
            set: { if let neu = $0 { model.selection = neu } }
        )
    }

    var body: some View {
        List(selection: markiert) {
            if let schema = model.schema {
                Label("Alle Vorlagen", systemImage: "square.grid.2x2")
                    .badge(schema.models.count)
                    .tag(SidebarItem.alle)
                if !projektTreffer.isEmpty {
                    Section("Zuletzt") {
                        ForEach(projektTreffer) { p in
                            ProjektZeile(projekt: p)
                        }
                    }
                }
                Section("Vorlagen") {
                    ForEach(schema.bereiche) { bereich in
                        let n = schema.anzahl(in: bereich)
                        if n > 0 {
                            Label(bereich.name, systemImage: BereichSymbol.name(for: bereich.id))
                                .badge(n)
                                .tag(SidebarItem.bereich(bereich.id))
                        }
                    }
                }
            }
            Section("Bibliothek") {
                Label("Motive und Fotos", systemImage: "photo.on.rectangle.angled").tag(SidebarItem.ki)
                Label("Pakete", systemImage: "shippingbox").tag(SidebarItem.pakete)
            }
        }
        .listStyle(.sidebar)
        .searchable(text: $model.suche, placement: .sidebar, prompt: "Vorlagen suchen")
        .onChange(of: model.suche) { _, neu in
            // Wer sucht, will die Treffer sehen – egal wo er gerade ist.
            guard !neu.trimmingCharacters(in: .whitespaces).isEmpty else { return }
            switch model.selection {
            case .alle, .bereich: break
            default: model.selection = .alle
            }
        }
        .safeAreaInset(edge: .bottom, spacing: 0) {
            EinstellungenZeile()
        }
    }
}

/// „Einstellungen“ fest am unteren Rand der Seitenleiste, mit Abzeichen bei verfügbaren Updates.
@MainActor
private struct EinstellungenZeile: View {
    @EnvironmentObject var model: AppModel

    private var aktiv: Bool { model.selection == .material || model.selection == .updates }

    var body: some View {
        VStack(spacing: 0) {
            Divider()
            Button {
                model.selection = model.updateCount > 0 ? .updates : .material
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "gearshape").frame(width: 18)
                    Text("Einstellungen")
                    Spacer()
                    if model.updateCount > 0 {
                        Text("\(model.updateCount)")
                            .font(.caption2.weight(.semibold))
                            .foregroundStyle(.white)
                            .padding(.horizontal, 6).padding(.vertical, 1)
                            .background(Theme.accent, in: Capsule())
                    }
                }
                .padding(.horizontal, 10).padding(.vertical, 6)
                .background(aktiv ? Color.primary.opacity(0.1) : .clear, in: RoundedRectangle(cornerRadius: 6))
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .padding(8)
        }
        .background(.bar)
    }
}

/// Linien-Symbole der Bereiche in der Seitenleiste.
enum BereichSymbol {
    static func name(for id: String) -> String {
        switch id {
        case "feste": return "snowflake"
        case "zuhause": return "house"
        case "spielen": return "die.face.5"
        case "formen": return "square.on.circle"
        case "markt": return "tag"
        case "basis": return "ruler"
        default: return "shippingbox"
        }
    }
}

/// Ein Projekt in „Zuletzt“: Klick öffnet es, Rechtsklick bietet Löschen.
@MainActor
private struct ProjektZeile: View {
    @EnvironmentObject var model: AppModel
    let projekt: Projekt

    var body: some View {
        Button {
            model.openProject(projekt)
        } label: {
            HStack {
                Label(projekt.name, systemImage: "doc")
                    .lineLimit(1)
                Spacer(minLength: 6)
                Text(kurzesDatum(projekt.geaendert))
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .fontWeight(model.projekt?.name == projekt.name ? .semibold : .regular)
        .help(model.schema?.models[projekt.model]?.label ?? projekt.model)
        .contextMenu {
            Button("Öffnen") { model.openProject(projekt) }
            Button("Löschen", role: .destructive) { Task { await model.deleteProject(projekt) } }
        }
    }

    private func kurzesDatum(_ sekunden: Double) -> String {
        let d = Date(timeIntervalSince1970: sekunden), cal = Calendar.current
        if cal.isDateInToday(d) { return "heute" }
        if cal.isDateInYesterday(d) { return "gestern" }
        let f = DateFormatter()
        f.locale = Locale(identifier: "de_DE")
        f.setLocalizedDateFormatFromTemplate(abs(d.timeIntervalSinceNow) < 6 * 86400 ? "EEE" : "d. MMM")
        return f.string(from: d)
    }
}

@MainActor
private struct DetailView: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        switch model.selection {
        case .model(let id):
            if let info = model.schema?.models[id] {
                WorkspaceView(modelID: id, info: info)
            } else {
                placeholder("Diese Vorlage gibt es nicht mehr.")
            }
        case .pakete:
            PackagesView()
        case .ki:
            KIView()
        case .material, .updates:
            EinstellungenView()
        case .alle:
            GalerieView(bereichID: nil)
        case .bereich(let id):
            GalerieView(bereichID: id)
        case nil:
            GalerieView(bereichID: nil)
        }
    }

    private func placeholder(_ text: String) -> some View {
        Text(text)
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

/// Engine-Status in der Werkzeugleiste: lädt / läuft / gestoppt.
@MainActor
struct EngineStatusBadge: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(color)
                .frame(width: 8, height: 8)
            Text(text)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .help(model.engineVersion.map { "Engine \($0)" } ?? "Engine")
    }

    private var text: String {
        switch model.engineState {
        case .starting: return "Engine lädt"
        case .running: return model.isBuilding ? "Engine baut …" : "Engine läuft"
        case .failed: return "Engine gestoppt"
        }
    }

    private var color: Color {
        switch model.engineState {
        case .starting: return Theme.warning
        case .running: return Theme.ok
        case .failed: return Theme.error
        }
    }
}
