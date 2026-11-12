import SteckwerkCore
import SwiftUI

/// Vorschaubild einer Platte (still, ohne Zoom): Holz, helle Teile, blaue Gravur.
struct PlattenBild: View {
    let geometry: SheetGeometry

    var body: some View {
        Canvas { context, size in
            guard geometry.width > 0, geometry.height > 0 else { return }
            let margin: CGFloat = 8
            let scale = max(min((size.width - 2 * margin) / geometry.width, (size.height - 2 * margin) / geometry.height), 0.01)
            let ox = (size.width - geometry.width * scale) / 2
            let oy = (size.height - geometry.height * scale) / 2
            let frame = CGRect(x: ox, y: oy, width: geometry.width * scale, height: geometry.height * scale)
            context.fill(Path(frame), with: .color(Theme.ply))
            var cut = Path(), engrave = Path()
            for line in geometry.lines {
                guard let first = line.points.first else { continue }
                var path = Path()
                path.move(to: CGPoint(x: ox + first.x * scale, y: oy + first.y * scale))
                for p in line.points.dropFirst() { path.addLine(to: CGPoint(x: ox + p.x * scale, y: oy + p.y * scale)) }
                if line.closed { path.closeSubpath() }
                if line.kind == .engrave { engrave.addPath(path) } else { cut.addPath(path) }
            }
            context.fill(cut, with: .color(Theme.part), style: FillStyle(eoFill: true))
            context.stroke(engrave, with: .color(Theme.engrave.opacity(0.85)), lineWidth: 0.5)
            context.stroke(cut, with: .color(Theme.cutLine.opacity(0.6)), lineWidth: 0.6)
        }
    }
}

/// Eine Vorlage als Kachel: Platten-Vorschau, Name, eine Zeile Beschreibung.
@MainActor
private struct VorlagenKachel: View {
    @EnvironmentObject var model: AppModel
    let entry: ModelEntry
    @State private var geometry: SheetGeometry?
    @State private var darueber = false

    var body: some View {
        Button {
            model.selection = .model(entry.id)
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                ZStack {
                    Theme.paper
                    if let geometry {
                        PlattenBild(geometry: geometry).transition(.opacity)
                    } else {
                        Image(systemName: GroupSymbol.name(for: entry.info.group))
                            .font(.title)
                            .foregroundStyle(.quaternary)
                    }
                }
                .aspectRatio(4.0 / 3.0, contentMode: .fit)
                .clipShape(RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.primary.opacity(darueber ? 0.22 : 0.08)))
                VStack(alignment: .leading, spacing: 2) {
                    Text(entry.info.label)
                        .font(.callout.weight(.medium))
                        .lineLimit(1)
                    Text(entry.info.desc)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                .padding(.horizontal, 2)
            }
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .onHover { darueber = $0 }
        .help(entry.info.desc)
        .task(id: entry.id) {
            let g = await model.vorschau(for: entry.id)
            withAnimation(.easeOut(duration: 0.18)) { geometry = g }
        }
    }
}

private struct Abschnitt: Identifiable {
    let titel: String
    let eintraege: [ModelEntry]
    var id: String { titel }
}

/// Galerie der Vorlagen: alle, eines Bereichs oder die Treffer der Suche – nach Themen gegliedert.
@MainActor
struct GalerieView: View {
    @EnvironmentObject var model: AppModel
    let bereichID: String?
    @State private var themaID: String?

    private let spalten = [GridItem(.adaptive(minimum: 176, maximum: 240), spacing: 18, alignment: .top)]

    private var schema: Schema? { model.schema }
    private var suchtext: String { model.suche.trimmingCharacters(in: .whitespaces) }

    private var bereiche: [Bereich] {
        guard let schema else { return [] }
        if let bereichID { return schema.bereiche.filter { $0.id == bereichID } }
        return schema.bereiche
    }

    private var titel: String {
        if !suchtext.isEmpty { return "Suche" }
        return bereichID.flatMap { id in schema?.bereiche.first { $0.id == id }?.name } ?? "Alle Vorlagen"
    }

    /// Abschnitte (Überschrift, Vorlagen), je nach Suche, Bereich und Themenfilter.
    private var abschnitte: [Abschnitt] {
        guard let schema else { return [] }
        if !suchtext.isEmpty {
            let treffer = Schema.filter(schema.alleModelle, matching: suchtext)
            return treffer.isEmpty ? [] : [Abschnitt(titel: "\(treffer.count) Treffer für „\(suchtext)“", eintraege: treffer)]
        }
        var result: [Abschnitt] = []
        for bereich in bereiche {
            for thema in bereich.themen where themaID == nil || thema.id == themaID {
                let e = schema.modelle(in: thema)
                if !e.isEmpty { result.append(Abschnitt(titel: bereichID == nil ? "\(bereich.name) · \(thema.name)" : thema.name, eintraege: e)) }
            }
        }
        return result
    }

    private var themen: [Thema] {
        guard suchtext.isEmpty, bereichID != nil else { return [] }
        return (bereiche.first?.themen ?? []).filter { !(schema?.modelle(in: $0).isEmpty ?? true) }
    }

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 26, pinnedViews: []) {
                kopf
                if abschnitte.isEmpty {
                    Text(suchtext.isEmpty ? "Hier gibt es noch keine Vorlagen." : "Keine Vorlage gefunden.")
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, minHeight: 160)
                }
                ForEach(abschnitte) { abschnitt in
                    VStack(alignment: .leading, spacing: 12) {
                        if abschnitte.count > 1 || !suchtext.isEmpty {
                            HStack(alignment: .firstTextBaseline) {
                                Text(abschnitt.titel).font(.headline)
                                if suchtext.isEmpty {
                                    Text("\(abschnitt.eintraege.count)").font(.subheadline).foregroundStyle(.tertiary)
                                }
                            }
                        }
                        LazyVGrid(columns: spalten, alignment: .leading, spacing: 20) {
                            ForEach(abschnitt.eintraege) { entry in
                                VorlagenKachel(entry: entry)
                            }
                        }
                    }
                }
            }
            .padding(.horizontal, 28)
            .padding(.vertical, 22)
        }
        .background(Theme.canvas)
        .navigationTitle(titel)
        .onChange(of: bereichID) { themaID = nil }
    }

    @ViewBuilder
    private var kopf: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(titel).font(.title2.weight(.semibold))
            if themen.count > 1 {
                Picker("Thema", selection: $themaID) {
                    Text("Alle").tag(String?.none)
                    ForEach(themen) { Text($0.name).tag(String?.some($0.id)) }
                }
                .pickerStyle(.segmented)
                .labelsHidden()
                .fixedSize()
            }
        }
    }
}

/// Einstellungen: Material und Updates unter einem Dach.
@MainActor
struct EinstellungenView: View {
    @EnvironmentObject var model: AppModel

    private var tab: Binding<SidebarItem> {
        Binding(get: { model.selection == .updates ? .updates : .material },
                set: { model.selection = $0 })
    }

    var body: some View {
        VStack(spacing: 0) {
            Picker("Bereich", selection: tab) {
                Text("Material").tag(SidebarItem.material)
                Text(model.updateCount > 0 ? "Updates (\(model.updateCount))" : "Updates").tag(SidebarItem.updates)
            }
            .pickerStyle(.segmented)
            .labelsHidden()
            .frame(maxWidth: 280)
            .padding(.top, 14)
            if model.selection == .updates {
                AppUpdateView()
            } else {
                MaterialView()
            }
        }
        .navigationTitle("Einstellungen")
    }
}
