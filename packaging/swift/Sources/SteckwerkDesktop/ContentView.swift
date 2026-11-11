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
    @State var suche = ""
    @AppStorage("offeneGruppen") private var offenRaw = ""

    private var offen: Set<String> { Set(offenRaw.split(separator: "\n").map(String.init)) }

    private func istOffen(_ group: ModelGroup) -> Binding<Bool> {
        Binding(
            get: {
                !suche.isEmpty || offen.contains(group.id) || group.models.contains { model.selectedModelID == $0.id }
            },
            set: { neu in
                var s = offen
                if neu { s.insert(group.id) } else { s.remove(group.id) }
                offenRaw = s.sorted().joined(separator: "\n")
            }
        )
    }

    private var projektTreffer: [Projekt] {
        let q = suche.trimmingCharacters(in: .whitespaces).lowercased()
        return q.isEmpty ? Array(model.projekte.prefix(4)) : model.projekte.filter { $0.name.lowercased().contains(q) }
    }

    var body: some View {
        List(selection: $model.selection) {
            if !projektTreffer.isEmpty {
                Section("Zuletzt") {
                    ForEach(projektTreffer) { p in
                        ProjektZeile(projekt: p)
                    }
                }
            }
            if let schema = model.schema {
                Section("Vorlagen") {
                    ForEach(schema.sidebarGroups(matching: suche)) { group in
                        DisclosureGroup(isExpanded: istOffen(group)) {
                            ForEach(group.models) { entry in
                                Text(entry.info.label)
                                    .tag(SidebarItem.model(entry.id))
                                    .help(entry.info.desc)
                            }
                        } label: {
                            Label(group.label, systemImage: GroupSymbol.name(for: group.id))
                                .badge(istOffen(group).wrappedValue ? 0 : group.models.count)
                        }
                    }
                }
            }
            Section("Werkstatt") {
                Label("Material", systemImage: "ruler").tag(SidebarItem.material)
                Label("Pakete", systemImage: "shippingbox").tag(SidebarItem.pakete)
                Label("Assistent und Motive", systemImage: "wand.and.stars").tag(SidebarItem.ki)
                Label("Updates", systemImage: "arrow.down.circle")
                    .badge(model.updateCount)
                    .tag(SidebarItem.updates)
            }
        }
        .listStyle(.sidebar)
        .searchable(text: $suche, placement: .sidebar, prompt: "Suchen")
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
        case .material:
            MaterialView()
        case .updates:
            AppUpdateView()
        case nil:
            placeholder("Links eine Vorlage wählen.")
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
