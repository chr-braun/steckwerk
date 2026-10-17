import SteckwerkCore
import SwiftUI

/// Prüfbericht nativ: Zeilen grün/orange/rot, darunter die Montagehinweise.
struct ReportView: View {
    @Environment(\.dismiss) private var dismiss
    let result: GenerateResult?

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Text("Prüfbericht").font(.title2.weight(.semibold))
                Spacer()
                if let r = result {
                    Label(r.statusLine, systemImage: r.ok ? "checkmark.seal.fill" : "xmark.octagon.fill")
                        .foregroundStyle(r.ok ? Theme.ok : Theme.fehler)
                }
                Button("Fertig") { dismiss() }.keyboardShortcut(.defaultAction)
            }
            .padding()
            Divider()
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    if let err = result?.error {
                        Text(err).foregroundStyle(Theme.fehler)
                    }
                    ForEach(result?.assemblies ?? []) { a in
                        Card {
                            VStack(alignment: .leading, spacing: 6) {
                                Text(a.summary).font(.headline).foregroundStyle(a.ok ? Theme.ok : Theme.fehler)
                                Text("\(a.parts) Teile · \(a.joints) Verbindungen")
                                    .font(.caption).foregroundStyle(.secondary)
                                ForEach(Array(a.reportLines.enumerated()), id: \.offset) { _, line in
                                    if !line.text.trimmingCharacters(in: .whitespaces).isEmpty {
                                        Text(line.text)
                                            .font(.system(.caption, design: .monospaced))
                                            .foregroundStyle(color(line.level))
                                            .textSelection(.enabled)
                                    }
                                }
                                if !a.notes.isEmpty {
                                    Divider().padding(.vertical, 4)
                                    Text("Montage").font(.subheadline.weight(.semibold))
                                    ForEach(a.notes, id: \.self) { n in
                                        Label(n, systemImage: "wrench.and.screwdriver")
                                            .font(.callout)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding()
            }
        }
        .background(Theme.paper)
    }

    private func color(_ l: ReportLine.Level) -> Color {
        switch l {
        case .ok: return Theme.ok
        case .warnung: return Theme.warnung
        case .fehler: return Theme.fehler
        case .info: return .primary
        }
    }
}
