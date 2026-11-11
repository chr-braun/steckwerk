import AppKit
import SteckwerkCore
import SwiftUI

/// „Eigene Gravur“ im Inspektor: Foto/Logo, Motiv oder Muster auf ein Teil des Modells gravieren.
@MainActor
struct GravurSection: View {
    @EnvironmentObject var model: AppModel
    let modelID: String

    var body: some View {
        let list = model.gravurListe(for: modelID)
        let optionen = model.schema?.gravur ?? GravurOptionen()
        Section {
            ForEach(Array(list.enumerated()), id: \.element.id) { index, eintrag in
                GravurRow(modelID: modelID, index: index, eintrag: binding(index), optionen: optionen)
            }
            HStack {
                Button("+ Foto/Logo") {
                    Task {
                        if model.bilder.isEmpty {
                            guard let id = await model.importFoto() else { return }
                            var g = GravurEintrag(quelle: "bild")
                            g.bild = id
                            add(g)
                        } else {
                            var g = GravurEintrag(quelle: "bild")
                            g.bild = model.bilder.first?.id ?? ""
                            add(g)
                        }
                    }
                }
                Button("+ Motiv") { add(GravurEintrag(quelle: "motiv")) }
                Button("+ Muster") { add(GravurEintrag(quelle: "muster")) }
            }
            .disabled(list.count >= optionen.max)
        } header: {
            Text("Eigene Gravur")
        } footer: {
            Text(list.isEmpty
                 ? "Eigenes Foto, Logo, Motiv oder Muster auf ein Teil gravieren – geht bei jedem Modell."
                 : "Fotos werden als Bild-Ebene graviert (in XCS „Gravieren“), Motive und Muster als Linien – nie über Schnitte oder Steckverbindungen.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private func add(_ g: GravurEintrag) {
        var list = model.gravurListe(for: modelID)
        list.append(g)
        model.setGravuren(list, for: modelID)
    }

    private func binding(_ index: Int) -> Binding<GravurEintrag> {
        Binding(
            get: {
                let list = model.gravurListe(for: modelID)
                return list.indices.contains(index) ? list[index] : GravurEintrag(quelle: "muster")
            },
            set: { neu in
                var list = model.gravurListe(for: modelID)
                guard list.indices.contains(index) else { return }
                list[index] = neu
                model.setGravuren(list, for: modelID)
            }
        )
    }
}

@MainActor
struct GravurRow: View {
    @EnvironmentObject var model: AppModel
    let modelID: String
    let index: Int
    @Binding var eintrag: GravurEintrag
    let optionen: GravurOptionen
    @State private var offen = true

    var body: some View {
        DisclosureGroup(isExpanded: $offen) {
            VStack(alignment: .leading, spacing: 8) {
                quelle
                lage
                HStack {
                    Toggle("eingeschaltet", isOn: $eintrag.aktiv)
                    Spacer()
                    Button("Entfernen", role: .destructive) {
                        var list = model.gravurListe(for: modelID)
                        if list.indices.contains(index) { list.remove(at: index) }
                        model.setGravuren(list, for: modelID)
                    }
                }
            }
            .padding(.top, 4)
        } label: {
            Text("\(index + 1) · \(titel)")
        }
    }

    private var titel: String {
        switch eintrag.quelle {
        case "bild": return "Foto · " + (model.bilder.first { $0.id == eintrag.bild }?.name ?? "bitte wählen")
        case "motiv": return "Motiv · " + (model.schema?.motive.first { $0.id == eintrag.motiv }?.name ?? "bitte wählen")
        default: return "Muster · " + (optionen.muster.first { $0.value.stringValue == eintrag.muster }?.label ?? eintrag.muster)
        }
    }

    @ViewBuilder
    private var quelle: some View {
        switch eintrag.quelle {
        case "bild":
            FotoGridPicker(selection: $eintrag.bild)
            Button("Foto oder Logo hinzufügen …") {
                Task { if let id = await model.importFoto() { eintrag.bild = id } }
            }
            auswahl("Gravur", optionen.modi, $eintrag.modus)
            auswahl("Bildform", optionen.formen, $eintrag.form)
            zahl("Helligkeit", $eintrag.helligkeit, -100...100, 5)
            zahl("Kontrast", $eintrag.kontrast, -100...100, 5)
            zahl("Gamma", $eintrag.gamma, 0.3...3, 0.1)
            Toggle("Umkehren (Negativ)", isOn: $eintrag.invertieren)
            Picker("Auflösung", selection: $eintrag.aufloesung) {
                ForEach(optionen.aufloesungen, id: \.self) { v in
                    Text("\(v.formatted()) Punkte/mm (\(Int((v * 25.4).rounded())) dpi)").tag(v)
                }
            }
        case "motiv":
            MotivGridPicker(selection: $eintrag.motiv, motive: model.schema?.motive ?? [])
                .frame(height: 200)
            auswahl("Gravur", optionen.motivArten, $eintrag.art)
            if eintrag.art == "flaeche" {
                zahl("Linienabstand", $eintrag.schraffur, 0.08...3, 0.05, einheit: "mm")
            }
        default:
            auswahl("Muster", optionen.muster, $eintrag.muster)
            zahl("Rapport", $eintrag.abstand, 1.5...60, 0.5, einheit: "mm")
            Stepper("Variante \(eintrag.seed)", value: $eintrag.seed, in: 0...99999)
        }
    }

    @ViewBuilder
    private var lage: some View {
        Picker("Auf Teil", selection: $eintrag.teil) {
            Text("größtes Teil").tag("auto")
            Text("alle Teile").tag("alle")
            ForEach(model.teile(for: modelID), id: \.name) { t in
                Text("\(t.name) (\(Int(t.w)) × \(Int(t.h)))").tag(t.name)
            }
            if !["auto", "alle"].contains(eintrag.teil) && !model.teile(for: modelID).contains(where: { $0.name == eintrag.teil }) {
                Text(eintrag.teil).tag(eintrag.teil)
            }
        }
        zahl(eintrag.quelle == "muster" ? "Bereich (0 = ganz)" : "Größe (0 = passend)", $eintrag.groesse, 0...1000, 1, einheit: "mm")
        if eintrag.quelle == "muster" && eintrag.groesse > 0 {
            auswahl("Bereichsform", optionen.bereiche, $eintrag.bereich)
        }
        zahl("nach rechts", $eintrag.x, -1000...1000, 1, einheit: "mm")
        zahl("nach oben", $eintrag.y, -1000...1000, 1, einheit: "mm")
        zahl("Drehung", $eintrag.drehung, -360...360, 5, einheit: "°")
        if eintrag.quelle != "muster" {
            Toggle("Spiegeln", isOn: $eintrag.spiegeln)
        }
        zahl("Randabstand", $eintrag.rand, 0...20, 0.5, einheit: "mm")
    }

    private func auswahl(_ titel: String, _ opts: [ParamOption], _ wert: Binding<String>) -> some View {
        Picker(titel, selection: wert) {
            ForEach(opts, id: \.self) { o in
                Text(o.label).tag(o.value.stringValue ?? o.value.displayText)
            }
        }
    }

    private func zahl(_ titel: String, _ wert: Binding<Double>, _ bereich: ClosedRange<Double>, _ schritt: Double,
                      einheit: String = "") -> some View {
        LabeledContent(titel) {
            HStack(spacing: 6) {
                TextField(titel, value: wert, format: .number.precision(.fractionLength(0...2)))
                    .labelsHidden()
                    .multilineTextAlignment(.trailing)
                    .frame(width: 70)
                    .textFieldStyle(.roundedBorder)
                Stepper(titel, value: wert, in: bereich, step: schritt)
                    .labelsHidden()
                if !einheit.isEmpty {
                    Text(einheit).foregroundStyle(.secondary).frame(minWidth: 20, alignment: .leading)
                }
            }
        }
    }
}

/// Fotos und Logos der Bild-Bibliothek als Raster.
@MainActor
struct FotoGridPicker: View {
    @EnvironmentObject var model: AppModel
    @Binding var selection: String
    private let columns = [GridItem(.adaptive(minimum: 80, maximum: 110), spacing: 8)]

    var body: some View {
        if model.bilder.isEmpty {
            Text("Noch keine Fotos – „Foto oder Logo hinzufügen …“")
                .foregroundStyle(.secondary)
        } else {
            LazyVGrid(columns: columns, spacing: 8) {
                ForEach(model.bilder) { bild in
                    Button {
                        selection = bild.id
                    } label: {
                        VStack(spacing: 2) {
                            if let data = bild.vorschauDaten, let image = NSImage(data: data) {
                                Image(nsImage: image)
                                    .resizable()
                                    .scaledToFit()
                                    .frame(width: 72, height: 56)
                            } else {
                                Image(systemName: "photo").frame(width: 72, height: 56)
                            }
                            Text(bild.name).font(.caption2).lineLimit(1)
                        }
                        .padding(4)
                        .background(RoundedRectangle(cornerRadius: 6)
                            .fill(selection == bild.id ? Color.accentColor.opacity(0.18) : Color.clear))
                        .overlay(RoundedRectangle(cornerRadius: 6)
                            .stroke(selection == bild.id ? Color.accentColor : Color.primary.opacity(0.12)))
                    }
                    .buttonStyle(.plain)
                    .contextMenu {
                        Button("Aus der Bibliothek löschen", role: .destructive) {
                            Task { await model.entferneFoto(bild.id) }
                        }
                    }
                }
            }
        }
    }
}
