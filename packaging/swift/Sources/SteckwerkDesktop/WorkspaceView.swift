import SteckwerkCore
import SwiftUI

/// Arbeitsfläche einer Vorlage: Platte in der Mitte, Statusleiste darunter, Werte im Inspektor rechts.
/// Die Werkzeugleiste trägt nur Material und den Hauptknopf „An xTool senden“.
@MainActor
struct WorkspaceView: View {
    @EnvironmentObject var model: AppModel
    let modelID: String
    let info: ModelInfo

    private var result: GenerateResponse? {
        model.resultModelID == modelID ? model.result : nil
    }

    var body: some View {
        VStack(spacing: 0) {
            canvas
            Divider()
            StatusBar(result: result)
        }
        .background(Theme.canvas)
        .navigationTitle(model.projekt?.name ?? info.label)
        .navigationSubtitle(subtitle)
        .inspector(isPresented: $model.showInspector) {
            ParameterForm(modelID: modelID, info: info)
                .inspectorColumnWidth(min: 280, ideal: 320, max: 440)
        }
        .toolbar { toolbar }
        .sheet(isPresented: $model.showReport) {
            if let result { ReportSheet(result: result).environmentObject(model) }
        }
        .sheet(isPresented: $model.showExport) {
            ExportSheet(modelID: modelID, title: model.projekt?.name ?? info.label)
                .environmentObject(model)
        }
        .sheet(isPresented: $model.showSaveProject) {
            SaveProjectSheet(vorschlag: model.projekt?.name ?? info.label)
                .environmentObject(model)
        }
    }

    private var subtitle: String {
        if let p = model.projekt {
            return "Vorlage \(info.label) · " + (p.geaendert ? "geändert" : "gesichert")
        }
        return model.schema?.groupLabels[info.group] ?? info.group
    }

    @ToolbarContentBuilder
    private var toolbar: some ToolbarContent {
        ToolbarItemGroup(placement: .primaryAction) {
            MaterialMenu()
            Button {
                model.showExport = true
            } label: {
                Label("An xTool senden", systemImage: "square.and.arrow.down.on.square")
                    .labelStyle(.titleAndIcon)
            }
            .buttonStyle(.borderedProminent)
            .disabled(!model.canExport)
            .help("Ausgeben: in xTool Creative Space öffnen oder Dateien sichern (⌘E)")
        }
    }

    @ViewBuilder
    private var canvas: some View {
        if let result, !result.assemblies.isEmpty {
            let all = result.assemblies.flatMap { a in a.sheets.map { (a, $0) } }
            let index = min(model.selectedSheet, max(all.count - 1, 0))
            VStack(spacing: 10) {
                if all.count > 1 {
                    Picker("Platte", selection: $model.selectedSheet) {
                        ForEach(all.indices, id: \.self) { i in
                            Text(sheetTitle(all, i)).tag(i)
                        }
                    }
                    .pickerStyle(.segmented)
                    .labelsHidden()
                    .fixedSize()
                }
                if let bad = result.assemblies.first(where: { !$0.ok }) {
                    ProblemBanner(assembly: bad)
                }
                if model.geometry.indices.contains(index) {
                    PreviewCanvas(geometry: model.geometry[index], checked: all[index].1.checked)
                } else {
                    Spacer()
                }
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 20)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else if let result, let error = result.error {
            ProblemBanner(text: error)
                .padding(24)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        } else {
            VStack(spacing: 10) {
                ProgressView()
                Text("Steckwerk rechnet die Platte …")
                    .foregroundStyle(.secondary)
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }

    private func sheetTitle(_ all: [(Assembly, SheetResult)], _ i: Int) -> String {
        let multiAsm = Set(all.map { $0.0.name }).count > 1
        if multiAsm {
            let same = all.filter { $0.0.name == all[i].0.name }
            let n = (same.firstIndex { $0.1.file == all[i].1.file } ?? 0) + 1
            return same.count > 1 ? "\(all[i].0.name) · \(n)" : all[i].0.name
        }
        return "Platte \(i + 1)"
    }
}

/// Rote Hinweiskarte, wenn eine Eingabe oder ein Teil nicht passt.
@MainActor
private struct ProblemBanner: View {
    var assembly: Assembly?
    var text: String?

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(Theme.error)
            VStack(alignment: .leading, spacing: 4) {
                Text(assembly == nil ? "Das geht so nicht" : "Nicht schnittfertig – es entsteht keine Datei")
                    .fontWeight(.semibold)
                if let text { Text(text).textSelection(.enabled) }
                if let assembly {
                    ForEach(Array(assembly.errors.prefix(4).enumerated()), id: \.offset) { _, e in
                        Text(e.replacingOccurrences(of: "FEHLER", with: "").trimmingCharacters(in: .whitespaces))
                            .font(.callout)
                            .foregroundStyle(.secondary)
                            .textSelection(.enabled)
                    }
                }
            }
            Spacer(minLength: 0)
        }
        .padding(12)
        .frame(maxWidth: 640)
        .background(Theme.paper, in: RoundedRectangle(cornerRadius: Theme.cornerRadius))
        .overlay(alignment: .leading) {
            UnevenRoundedRectangle(topLeadingRadius: Theme.cornerRadius, bottomLeadingRadius: Theme.cornerRadius)
                .fill(Theme.error).frame(width: 3)
        }
        .shadow(color: .black.opacity(0.06), radius: 6, y: 2)
    }
}

/// Statusleiste: Prüfstatus (öffnet den Prüfbericht), Teile und Platten, Laserzeit, Datei.
@MainActor
struct StatusBar: View {
    @EnvironmentObject var model: AppModel
    let result: GenerateResponse?

    var body: some View {
        HStack(spacing: 12) {
            Button {
                if result != nil { model.showReport = true }
            } label: {
                HStack(spacing: 7) {
                    if busy {
                        ProgressView().controlSize(.mini)
                    } else {
                        Circle().fill(color).frame(width: 7, height: 7)
                    }
                    Text(statusText)
                        .fontWeight(.medium)
                        .foregroundStyle(busy ? Color.secondary : color)
                }
                .contentShape(Rectangle())
            }
            .buttonStyle(.plain)
            .help("Prüfbericht und Zusammenbau")

            if let result, result.error == nil, !result.assemblies.isEmpty {
                Divider().frame(height: 14)
                Text(partsText(result))
                if let e = model.estimate {
                    Divider().frame(height: 14)
                    Label {
                        Text("ca. \(e.zeit) Laser" + (e.kosten.map { String(format: " · ca. %.2f € Material", $0)
                            .replacingOccurrences(of: ".", with: ",") } ?? ""))
                    } icon: {
                        Image(systemName: "clock").foregroundStyle(.tertiary)
                    }
                    .help("Geschätzt für den xTool M2 mit den Startwerten des Materials")
                }
            }
            Spacer(minLength: 8)
            if let message = model.statusMessage {
                Text(message).foregroundStyle(.secondary).lineLimit(1)
            } else if let file = fileText {
                Text(file).foregroundStyle(.tertiary).lineLimit(1)
            }
        }
        .font(.callout)
        .monospacedDigit()
        .foregroundStyle(.secondary)
        .padding(.horizontal, 14)
        .frame(height: 30)
        .background(Theme.statusBar)
    }

    private var busy: Bool { model.isBuilding || model.isPreviewing || result == nil }

    private var good: Bool { result?.canExport == true }

    private var color: Color { good ? Theme.ok : Theme.error }

    private var statusText: String {
        if busy { return "Prüfe …" }
        guard let result else { return "Bereit" }
        if result.error != nil, result.assemblies.isEmpty { return "Eingabe prüfen" }
        return good ? (model.resultIsStale ? "Schnittfertig · Werte geändert" : "Schnittfertig") : "Fehler – keine Datei"
    }

    private func partsText(_ r: GenerateResponse) -> String {
        let parts = r.assemblies.reduce(0) { $0 + $1.parts }
        let sheets = r.assemblies.reduce(0) { $0 + $1.sheets.count }
        var t = "\(parts) Teile · \(sheets) \(sheets == 1 ? "Platte" : "Platten")"
        if sheets == 1, let e = model.estimate { t += ", \(e.ausnutzung) % genutzt" }
        return t
    }

    private var fileText: String? {
        guard let result else { return nil }
        let all = result.assemblies.flatMap(\.sheets)
        guard !all.isEmpty else { return nil }
        let s = all[min(model.selectedSheet, all.count - 1)]
        return "\(s.file) · \(Int(s.width)) × \(Int(s.height)) mm"
    }
}

/// Material-Menü in der Werkzeugleiste: gängige Stärken direkt, alles Weitere unter „Material“.
@MainActor
private struct MaterialMenu: View {
    @EnvironmentObject var model: AppModel

    var body: some View {
        Menu {
            ForEach([1.5, 2, 3, 4, 6], id: \.self) { t in
                Toggle(isOn: Binding(get: { abs(model.thickness - t) < 0.001 }, set: { _ in model.setThickness(t) })) {
                    Text(String(format: "%g mm", t).replacingOccurrences(of: ".", with: ","))
                }
            }
            Divider()
            Button("Material und Platte einstellen …") { model.selection = .material }
        } label: {
            Label {
                Text(model.materialSummary)
            } icon: {
                RoundedRectangle(cornerRadius: 3)
                    .fill(LinearGradient(colors: [Theme.part, Theme.ply], startPoint: .topLeading, endPoint: .bottomTrailing))
                    .frame(width: 12, height: 12)
            }
            .labelStyle(.titleAndIcon)
        }
        .fixedSize()
        .help("Material und Laser")
    }
}

/// Projekt sichern: Name eingeben, gleichnamige werden ersetzt.
@MainActor
private struct SaveProjectSheet: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    let vorschlag: String
    @State private var name = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Projekt sichern").font(.headline)
            Text("Ein Projekt merkt sich Vorlage, alle Werte und das Material. Du findest es in der Seitenleiste unter „Zuletzt“.")
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
            TextField("Name, z. B. Wichtelhaus für Oma", text: $name)
                .textFieldStyle(.roundedBorder)
                .onSubmit(save)
            HStack {
                Spacer()
                Button("Abbrechen", role: .cancel) { dismiss() }
                    .keyboardShortcut(.cancelAction)
                Button("Sichern", action: save)
                    .keyboardShortcut(.defaultAction)
                    .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
        .padding(20)
        .frame(width: 420)
        .onAppear { name = vorschlag }
    }

    private func save() {
        let n = name
        dismiss()
        Task { await model.saveProject(named: n) }
    }
}
