import SteckwerkCore
import SwiftUI

/// Prüfbericht als Blatt: Ergebnis in einem Satz, Teiletabelle mit Nummern, Zusammenbau,
/// darunter eingeklappt die technischen Prüfzeilen.
@MainActor
struct ReportSheet: View {
    @EnvironmentObject var model: AppModel
    @Environment(\.dismiss) private var dismiss
    let result: GenerateResponse
    @State private var assemblyIndex = 0

    private var assembly: Assembly? {
        result.assemblies.indices.contains(assemblyIndex) ? result.assemblies[assemblyIndex] : result.assemblies.first
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            header
            if result.assemblies.count > 1 {
                Picker("Baugruppe", selection: $assemblyIndex) {
                    ForEach(result.assemblies.indices, id: \.self) { i in
                        Text(result.assemblies[i].name).tag(i)
                    }
                }
                .pickerStyle(.segmented)
                .labelsHidden()
            }
            if let assembly {
                ScrollView {
                    VStack(alignment: .leading, spacing: 16) {
                        if !assembly.teile.isEmpty { PartsTable(assembly: assembly) }
                        if !assembly.notes.isEmpty { steps(assembly) }
                        TechnicalDetails(assembly: assembly)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            HStack {
                Spacer()
                Button("Fertig") { dismiss() }
                    .keyboardShortcut(.defaultAction)
            }
        }
        .padding(22)
        .frame(width: 620)
        .frame(minHeight: 420, idealHeight: 600, maxHeight: 760)
    }

    private var header: some View {
        let good = result.canExport
        return HStack(spacing: 12) {
            Image(systemName: good ? "checkmark" : "xmark")
                .font(.system(size: 16, weight: .bold))
                .foregroundStyle(good ? Theme.ok : Theme.error)
                .frame(width: 34, height: 34)
                .background(Circle().fill((good ? Theme.ok : Theme.error).opacity(0.13)))
            VStack(alignment: .leading, spacing: 2) {
                Text(good ? "Schnittfertig" : "Nicht schnittfertig")
                    .font(.headline)
                Text(lead)
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
    }

    private var lead: String {
        if let error = result.error, result.assemblies.isEmpty { return error }
        guard result.canExport else {
            return "Steckwerk erzeugt keine Datei, solange ein Teil nicht passt. Die Werte im Inspektor anpassen."
        }
        func de(_ v: Double) -> String { String(format: "%g", v).replacingOccurrences(of: ".", with: ",") }
        let parts = result.assemblies.reduce(0) { $0 + $1.parts }
        let joints = result.assemblies.reduce(0) { $0 + $1.joints }
        return "Alle \(parts) Teile sind geschlossen, \(joints) Steckverbindungen passen bei \(de(model.thickness)) mm "
            + "Material und \(de(model.kerf)) mm Kerf."
    }

    private func steps(_ assembly: Assembly) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Zusammenbau").font(.subheadline.weight(.semibold))
            ForEach(Array(assembly.notes.enumerated()), id: \.offset) { i, note in
                HStack(alignment: .firstTextBaseline, spacing: 10) {
                    Text("\(i + 1)")
                        .font(.caption.weight(.semibold))
                        .monospacedDigit()
                        .foregroundStyle(.secondary)
                        .frame(width: 20, height: 20)
                        .background(Circle().fill(Color.primary.opacity(0.07)))
                    Text(assembly.hinweis(note))
                        .fixedSize(horizontal: false, vertical: true)
                        .textSelection(.enabled)
                }
            }
        }
    }
}

/// Teile mit Nummer (wie eingraviert), Name, Größe und Prüfergebnis.
@MainActor
private struct PartsTable: View {
    let assembly: Assembly

    var body: some View {
        Grid(alignment: .leading, horizontalSpacing: 14, verticalSpacing: 0) {
            GridRow {
                Text("Teil"); Text("Name"); Text("Größe"); Text("Prüfung")
            }
            .font(.caption.weight(.semibold))
            .foregroundStyle(.secondary)
            .padding(.vertical, 6)
            ForEach(assembly.teile) { t in
                Divider().gridCellUnsizedAxes(.horizontal)
                GridRow {
                    PartNumber(nr: t.nr)
                    Text(t.anzeigeName(baugruppe: assembly.name))
                        .help(t.name)
                        .gridColumnAlignment(.leading)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    Text(t.groesse).monospacedDigit()
                    Label(t.ok ? "passt" : "Fehler", systemImage: t.ok ? "checkmark" : "xmark")
                        .foregroundStyle(t.ok ? Theme.ok : Theme.error)
                        .fontWeight(t.ok ? .regular : .semibold)
                }
                .padding(.vertical, 5)
            }
        }
        .padding(.horizontal, 12)
        .padding(.bottom, 4)
        .background(Theme.card, in: RoundedRectangle(cornerRadius: Theme.cornerRadius))
        .overlay(RoundedRectangle(cornerRadius: Theme.cornerRadius).stroke(Color.primary.opacity(0.08)))
    }
}

/// Die einzelnen Prüfzeilen des Validators – für die Fehlersuche, sonst eingeklappt.
@MainActor
private struct TechnicalDetails: View {
    let assembly: Assembly
    @State private var open = false
    @State private var onlyErrors = false

    var body: some View {
        DisclosureGroup("Technische Details", isExpanded: Binding(get: { open || !assembly.ok }, set: { open = $0 })) {
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("\(assembly.parts) Teile · \(assembly.joints) Verbindungen · \(assembly.sheets.count) \(assembly.sheets.count == 1 ? "Platte" : "Platten")")
                        .foregroundStyle(.secondary)
                    Spacer()
                    Toggle("nur Fehler", isOn: $onlyErrors).toggleStyle(.switch).controlSize(.mini)
                }
                .font(.caption)
                let lines = ReportFormatter.lines(assembly.report).filter { !onlyErrors || $0.status == .error }
                VStack(alignment: .leading, spacing: 2) {
                    if lines.isEmpty { Text("Keine Fehler.").foregroundStyle(.secondary) }
                    ForEach(Array(lines.enumerated()), id: \.offset) { _, line in
                        Text(line.text)
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(color(line.status))
                            .textSelection(.enabled)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(10)
                .background(Color.primary.opacity(0.04), in: RoundedRectangle(cornerRadius: 7))
            }
            .padding(.top, 6)
        }
        .foregroundStyle(.secondary)
    }

    private func color(_ status: ReportStatus) -> Color {
        switch status {
        case .ok: return .secondary
        case .error: return Theme.error
        case .warning: return Theme.warning
        case .info: return .primary
        }
    }
}
