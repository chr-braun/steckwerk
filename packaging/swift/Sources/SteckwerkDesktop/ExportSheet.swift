import SteckwerkCore
import SwiftUI

/// Ausgeben: zwei klare Wege – direkt in xTool Creative Space öffnen (empfohlen) oder Dateien sichern.
/// Darunter die Extras als Schalter und die Schätzung in Kacheln.
@MainActor
struct ExportSheet: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    let modelID: String
    let title: String

    enum Ziel: String { case xcs, dateien }
    enum Ort: String { case ordner, steckwerk }

    @AppStorage("ausgebenZiel") private var zielRaw = Ziel.xcs.rawValue
    @AppStorage("ausgebenOrt") private var ortRaw = Ort.ordner.rawValue

    private var ziel: Ziel { Ziel(rawValue: zielRaw) ?? .xcs }
    private var ort: Ort { Ort(rawValue: ortRaw) ?? .ordner }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 3) {
                Text("„\(title)“ ausgeben").font(.headline)
                Text(lead).foregroundStyle(.secondary)
            }

            VStack(spacing: 8) {
                ChoiceCard(selected: ziel == .xcs, action: { zielRaw = Ziel.xcs.rawValue }) {
                    HStack(spacing: 6) {
                        Text("In xTool Creative Space öffnen").fontWeight(.semibold)
                        Text("Empfohlen")
                            .font(.caption2.weight(.semibold))
                            .foregroundStyle(Color.accentColor)
                            .padding(.horizontal, 6).padding(.vertical, 1)
                            .background(Color.accentColor.opacity(0.13), in: RoundedRectangle(cornerRadius: 4))
                    }
                    Text("Schnitt und Ritzen liegen auf eigenen Ebenen, das Gerät ist der M2. Du prüfst nur noch die Laserwerte und startest.")
                        .font(.callout).foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
                ChoiceCard(selected: ziel == .dateien, action: { zielRaw = Ziel.dateien.rawValue }) {
                    HStack(alignment: .firstTextBaseline) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Dateien sichern").fontWeight(.semibold)
                            Text(ort == .ordner ? "SVGs und Prüfbericht in einen Ordner deiner Wahl."
                                                : "In den Steckwerk-Ordner, auf Wunsch mit XCS- und Studio-Projekt.")
                                .font(.callout).foregroundStyle(.secondary)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                        Spacer(minLength: 8)
                        Picker("Ort", selection: Binding(get: { ort }, set: { ortRaw = $0.rawValue; zielRaw = Ziel.dateien.rawValue })) {
                            Text("Ordner wählen …").tag(Ort.ordner)
                            Text("Steckwerk-Ordner").tag(Ort.steckwerk)
                        }
                        .labelsHidden()
                        .fixedSize()
                    }
                }
            }

            options

            if let e = model.estimate {
                FactsGrid(tiles: facts(e))
            }

            HStack {
                Button("Steckwerk-Ordner öffnen") { Task { await model.openFolder() } }
                    .buttonStyle(.link)
                Spacer()
                Button("Abbrechen", role: .cancel) { dismiss() }
                    .keyboardShortcut(.cancelAction)
                Button(primaryTitle, action: go)
                    .keyboardShortcut(.defaultAction)
                    .disabled(!model.canExport)
            }
        }
        .padding(22)
        .frame(width: 540)
    }

    private var lead: String {
        let sheets = model.result?.assemblies.reduce(0) { $0 + $1.sheets.count } ?? 0
        let parts = model.result?.assemblies.reduce(0) { $0 + $1.parts } ?? 0
        let w = model.material["sheet_width"]?.doubleValue ?? 400, h = model.material["sheet_height"]?.doubleValue ?? 300
        let platte = sheets == 1 ? "einer Platte" : "\(sheets) Platten"
        return "\(parts) Teile auf \(platte) \(Int(w)) × \(Int(h)) mm, \(model.materialSummary)."
    }

    @ViewBuilder
    private var options: some View {
        VStack(spacing: 0) {
            if let p = model.partNumbersParam {
                optionRow("Teilenummern klein eingravieren", isOn: Binding(
                    get: { model.materialBinding(for: p).wrappedValue.boolValue ?? false },
                    set: { model.materialBinding(for: p).wrappedValue = .bool($0) }))
            }
            if ziel == .xcs || ort == .steckwerk {
                Divider()
                optionRow("Montageanleitung als PDF dazulegen", isOn: format("pdf"))
            }
            if ziel == .dateien && ort == .steckwerk {
                Divider()
                optionRow("XCS-Projekt (.xcs) dazulegen", isOn: format("xcs"))
                Divider()
                optionRow("xTool-Studio-Projekt (.xs) dazulegen", isOn: format("xs"))
                    .help("xTool Studio ab 1.7 – mit Leistung, Tempo und Durchgängen je Ebene")
            }
        }
        .padding(.horizontal, 12)
        .background(Theme.card, in: RoundedRectangle(cornerRadius: Theme.cornerRadius))
        .overlay(RoundedRectangle(cornerRadius: Theme.cornerRadius).stroke(Color.primary.opacity(0.08)))
    }

    private func optionRow(_ title: String, isOn: Binding<Bool>) -> some View {
        Toggle(isOn: isOn) {
            Text(title).frame(maxWidth: .infinity, alignment: .leading)
        }
        .toggleStyle(.switch)
        .controlSize(.small)
        .padding(.vertical, 8)
    }

    private func format(_ f: String) -> Binding<Bool> {
        Binding(get: { model.exportFormate.contains(f) },
                set: { on in if on { model.exportFormate.insert(f) } else { model.exportFormate.remove(f) } })
    }

    private var primaryTitle: String {
        switch (ziel, ort) {
        case (.xcs, _): return "In XCS öffnen"
        case (.dateien, .ordner): return "Exportieren …"
        case (.dateien, .steckwerk): return "Sichern"
        }
    }

    private func facts(_ e: (zeit: String, schnitt: Double, ritzen: Double, ausnutzung: Int, kosten: Double?)) -> [(String, String)] {
        func de(_ v: Double) -> String { String(format: "%g", v).replacingOccurrences(of: ".", with: ",") }
        let sheets = model.result?.assemblies.reduce(0) { $0 + $1.sheets.count } ?? 0
        var t: [(String, String)] = [(e.zeit, "Laserzeit"), ("\(de(e.schnitt)) m", "Schnitt")]
        if e.ritzen > 0 { t.append(("\(de(e.ritzen)) m", "Ritzen")) }
        t.append(("\(sheets) \(sheets == 1 ? "Platte" : "Platten")", "\(e.ausnutzung) % genutzt"))
        if let k = e.kosten { t.append((String(format: "%.2f €", k).replacingOccurrences(of: ".", with: ","), "Material")) }
        return t
    }

    private func go() {
        let z = ziel, o = ort, pdf = model.exportFormate.contains("pdf")
        dismiss()
        Task {
            switch (z, o) {
            case (.xcs, _): await model.sendToXCS(withGuide: pdf)
            case (.dateien, .ordner): await model.exportToChosenFolder()
            case (.dateien, .steckwerk): await model.saveToEngineFolder()
            }
        }
    }
}

/// Auswahlkarte mit Radio-Punkt; die ganze Fläche ist klickbar.
@MainActor
private struct ChoiceCard<Content: View>: View {
    let selected: Bool
    let action: () -> Void
    @ViewBuilder let content: Content

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: selected ? "largecircle.fill.circle" : "circle")
                .font(.system(size: 15))
                .foregroundStyle(selected ? Color.accentColor : Color.secondary)
                .padding(.top, 1)
            VStack(alignment: .leading, spacing: 2) { content }
            Spacer(minLength: 0)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 11)
        .background(Theme.card, in: RoundedRectangle(cornerRadius: Theme.cornerRadius))
        .overlay(
            RoundedRectangle(cornerRadius: Theme.cornerRadius)
                .stroke(selected ? Color.accentColor : Color.primary.opacity(0.12), lineWidth: selected ? 2 : 1)
        )
        .contentShape(RoundedRectangle(cornerRadius: Theme.cornerRadius))
        .onTapGesture(perform: action)
        .accessibilityElement(children: .combine)
        .accessibilityAddTraits(selected ? [.isButton, .isSelected] : .isButton)
    }
}

/// Kennzahlen nebeneinander, getrennt durch feine Linien.
@MainActor
struct FactsGrid: View {
    let tiles: [(String, String)]

    var body: some View {
        HStack(spacing: 0) {
            ForEach(Array(tiles.enumerated()), id: \.offset) { i, tile in
                if i > 0 { Divider() }
                VStack(alignment: .leading, spacing: 1) {
                    Text(tile.0).font(.title3.weight(.semibold)).monospacedDigit()
                    Text(tile.1).font(.caption).foregroundStyle(.secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
            }
        }
        .fixedSize(horizontal: false, vertical: true)
        .background(Theme.card, in: RoundedRectangle(cornerRadius: Theme.cornerRadius))
        .overlay(RoundedRectangle(cornerRadius: Theme.cornerRadius).stroke(Color.primary.opacity(0.08)))
    }
}
