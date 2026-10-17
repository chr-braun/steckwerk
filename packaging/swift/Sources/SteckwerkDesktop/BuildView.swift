import SteckwerkCore
import SwiftUI

/// Mitte: Blattvorschau, Statuszeile, Prüfbericht und Montagehinweise.
struct BuildView: View {
    @Environment(AppModel.self) private var model
    let key: String
    let info: ModelInfo
    @State private var sheetIndex = 0
    @State private var showReport = false

    private var sheets: [(Assembly, Sheet)] {
        (model.result?.assemblies ?? []).flatMap { a in a.sheets.map { (a, $0) } }
    }

    var body: some View {
        VStack(spacing: 0) {
            header
            Divider()
            if let err = model.result?.error, model.resultKey?.model == key {
                ContentUnavailableView("Nicht baubar", systemImage: "xmark.octagon", description: Text(err))
            } else if model.resultKey?.model == key, !sheets.isEmpty {
                let idx = min(sheetIndex, sheets.count - 1)
                PreviewCanvas(drawing: sheets[idx].1.drawing,
                              cutColor: model.config["cut_color"]?.stringValue ?? "#000000",
                              checked: sheets[idx].1.checked)
                    .id(sheets[idx].1.file + (model.resultKey.map { "\($0.hashValue)" } ?? ""))
                if sheets.count > 1 {
                    Picker("Blatt", selection: $sheetIndex) {
                        ForEach(sheets.indices, id: \.self) { i in
                            Text(sheets[i].1.file.replacingOccurrences(of: ".svg", with: "")).tag(i)
                        }
                    }
                    .pickerStyle(.segmented)
                    .labelsHidden()
                    .padding(8)
                }
            } else {
                ProgressView("Baue „\(info.label)“ …")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .navigationTitle(info.label)
        .navigationSubtitle(subtitle)
        .toolbar {
            ToolbarItemGroup {
                Button { Task { await model.build() } } label: {
                    Label("Bauen & prüfen", systemImage: "hammer")
                }
                .help("Bauen & prüfen (⌘B)")
                Button { showReport = true } label: {
                    Label("Prüfbericht", systemImage: "checkmark.seal")
                }
                .disabled(model.result == nil)
                Button { model.exportWithPanel() } label: {
                    Label("Exportieren", systemImage: "square.and.arrow.down")
                }
                .disabled(!model.canExport)
                .help("SVG und Prüfbericht speichern (⌘E)")
            }
        }
        .sheet(isPresented: $showReport) {
            ReportView(result: model.result)
                .frame(minWidth: 640, minHeight: 480)
        }
        .onChange(of: key) { sheetIndex = 0 }
    }

    private var subtitle: String {
        let parts = sheets.map { $0.1.parts }.reduce(0, +)
        return "\(info.group) · \(parts) Teile"
    }

    private var header: some View {
        HStack(spacing: 10) {
            statusPill
            if let msg = model.message {
                Text(msg).font(.callout).foregroundStyle(.secondary).lineLimit(1)
            }
            Spacer()
            if let r = model.result {
                Text(String(format: "%.2f s", r.elapsed)).font(.caption).foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, Theme.padding)
        .padding(.vertical, 8)
    }

    @ViewBuilder private var statusPill: some View {
        if let r = model.result, model.resultKey?.model == key {
            Button { showReport = true } label: {
                Label(r.statusLine, systemImage: r.ok ? "checkmark.circle.fill" : "xmark.octagon.fill")
                    .font(.callout.weight(.semibold))
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .foregroundStyle(r.ok ? Theme.ok : Theme.fehler)
                    .background((r.ok ? Theme.ok : Theme.fehler).opacity(0.12), in: Capsule())
            }
            .buttonStyle(.plain)
            .help("Prüfbericht öffnen")
        } else {
            Label("noch nicht geprüft", systemImage: "circle.dashed")
                .font(.callout)
                .foregroundStyle(.secondary)
        }
    }
}
