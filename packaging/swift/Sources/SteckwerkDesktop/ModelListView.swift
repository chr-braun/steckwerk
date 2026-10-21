import SteckwerkCore
import SwiftUI

struct ContentView: View {
    @Environment(AppModel.self) private var model
    @State private var showInspector = true

    var body: some View {
        NavigationSplitView {
            ModelListView()
                .navigationSplitViewColumnWidth(min: 200, ideal: 240, max: 320)
        } detail: {
            detail
                .background(Theme.paper)
        }
        .toolbar {
            ToolbarItem(placement: .status) { EngineStatusView() }
        }
        .alert("Hinweis", isPresented: Binding(get: { model.errorText != nil }, set: { if !$0 { model.errorText = nil } })) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(model.errorText ?? "")
        }
        .tint(Theme.accent)
    }

    @ViewBuilder private var detail: some View {
        switch model.selection {
        case .modell(let key):
            if let m = model.schema?.models[key] {
                BuildView(key: key, info: m)
                    .inspector(isPresented: $showInspector) {
                        ParameterForm(info: m)
                            .inspectorColumnWidth(min: 280, ideal: 320, max: 420)
                    }
                    .toolbar {
                        ToolbarItem {
                            Button { showInspector.toggle() } label: {
                                Label("Werte", systemImage: "sidebar.right")
                            }
                            .help("Werte ein-/ausblenden")
                        }
                    }
            } else {
                ContentUnavailableView("Modell nicht gefunden", systemImage: "questionmark.square.dashed")
            }
        case .pakete: PackagesView()
        case .ki: KIView()
        case .material: MaterialView()
        case .updates: AppUpdateView()
        case nil: EngineStartView()
        }
    }
}

struct ModelListView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        @Bindable var model = model
        List(selection: Binding(get: { model.selection }, set: { if let s = $0 { model.select(s) } })) {
            if let s = model.schema {
                ForEach(s.orderedGroups, id: \.self) { g in
                    let items = s.models(in: g).filter(matches)
                    if !items.isEmpty {
                        Section(s.label(forGroup: g)) {
                            ForEach(items, id: \.key) { item in
                                Label(item.info.label, systemImage: icon(for: g))
                                    .help(item.info.desc)
                                    .tag(SidebarItem.modell(item.key))
                            }
                        }
                    }
                }
            }
            Section("Werkstatt") {
                Label("Pakete", systemImage: "shippingbox").tag(SidebarItem.pakete)
                Label("KI", systemImage: "sparkles").tag(SidebarItem.ki)
                Label("Material", systemImage: "square.stack.3d.up").tag(SidebarItem.material)
                Label("Updates", systemImage: "arrow.down.circle").tag(SidebarItem.updates)
            }
        }
        .listStyle(.sidebar)
        .searchable(text: $model.suche, placement: .sidebar, prompt: "Modell suchen")
    }

    private func matches(_ item: (key: String, info: ModelInfo)) -> Bool {
        let q = model.suche.trimmingCharacters(in: .whitespaces)
        if q.isEmpty { return true }
        return item.info.label.localizedCaseInsensitiveContains(q) || item.key.localizedCaseInsensitiveContains(q)
            || item.info.desc.localizedCaseInsensitiveContains(q)
    }

    private func icon(for group: String) -> String {
        let g = group.lowercased()
        if g.contains("haus") || g.contains("häuser") { return "house" }
        if g.contains("fahrzeug") { return "car" }
        if g.contains("schmuck") { return "sparkle" }
        if g.contains("motiv") { return "photo" }
        if g.contains("zubehör") { return "lamp.table" }
        if g.contains("komplett") { return "square.grid.2x2" }
        return "cube"
    }
}

struct EngineStatusView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        HStack(spacing: 6) {
            Circle().fill(color).frame(width: 8, height: 8)
            Text("Engine \(model.engineState.label)")
                .font(.callout)
                .foregroundStyle(.secondary)
            if model.busy { ProgressView().controlSize(.small) }
        }
        .help(help)
    }

    private var color: Color {
        switch model.engineState {
        case .laeuft: return Theme.ok
        case .laedt: return Theme.warnung
        case .gestoppt: return .gray
        case .fehler: return Theme.fehler
        }
    }

    private var help: String {
        if case .laeuft(let port, _, let eigen) = model.engineState {
            return eigen ? "Eigene Engine auf Port \(port)" : "Mitbenutzte Steckwerk-Engine auf Port \(port)"
        }
        return model.engineDetails ?? ""
    }
}

struct EngineStartView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        switch model.engineState {
        case .fehler(let msg):
            VStack(spacing: 12) {
                ContentUnavailableView("Engine startet nicht", systemImage: "exclamationmark.triangle",
                                       description: Text(msg.split(separator: "\n").first.map(String.init) ?? msg))
                DisclosureGroup("Details") {
                    ScrollView {
                        Text(model.engineDetails ?? msg)
                            .font(.system(.caption, design: .monospaced))
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                    .frame(maxHeight: 180)
                }
                .frame(maxWidth: 520)
                Button("Erneut versuchen") { Task { await model.restartEngine() } }
                    .buttonStyle(.borderedProminent)
            }
            .padding()
        default:
            ProgressView("Steckwerk-Engine startet …")
        }
    }
}
