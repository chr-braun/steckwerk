import SteckwerkCore
import SwiftUI

/// Formular aus schema.models[].params – Abschnitte aus `section`, Felder nach `type`.
struct ParameterForm: View {
    @Environment(AppModel.self) private var model
    let info: ModelInfo

    var body: some View {
        let values = model.values[model.selectedModelKey ?? ""] ?? info.defaults
        Form {
            ForEach(info.sections, id: \.title) { section in
                let visible = section.params.filter { $0.isVisible(values: values) }
                if !visible.isEmpty {
                    Section(section.title.isEmpty ? "Größe und Ausstattung" : section.title) {
                        ForEach(visible) { p in
                            ParamField(param: p)
                        }
                    }
                }
            }
            Section {
                Button("Standardwerte") { model.resetModel() }
            }
        }
        .formStyle(.grouped)
    }
}

struct ParamField: View {
    @Environment(AppModel.self) private var model
    let param: Param

    var body: some View {
        Group {
            switch param.type {
            case .number, .int: NumberField(param: param)
            case .bool:
                Toggle(param.label, isOn: Binding(
                    get: { model.value(param).boolValue ?? false },
                    set: { model.set(param, .bool($0)) }))
            case .select:
                Picker(param.label, selection: Binding(
                    get: { model.value(param).stringValue ?? "" },
                    set: { v in
                        let opt = param.options.first { $0.id == v }
                        model.set(param, opt?.value ?? .string(v))
                    })) {
                    ForEach(param.options) { o in Text(o.label).tag(o.id) }
                }
            case .text: TextParam(param: param)
            case .motiv: MotivPicker(param: param)
            case .motive: MotiveList(param: param)
            case .unknown:
                LabeledContent(param.label, value: model.value(param).stringValue ?? "–")
            }
        }
        .help(param.help)
    }
}

struct NumberField: View {
    @Environment(AppModel.self) private var model
    let param: Param

    var body: some View {
        let step = param.step ?? (param.type == .int ? 1 : 0.5)
        let value = model.value(param).doubleValue ?? 0
        LabeledContent(param.label) {
            HStack(spacing: 6) {
                TextField("", value: Binding(get: { value }, set: { model.set(param, .number($0)) }),
                          format: .number.precision(.fractionLength(0...(param.type == .int ? 0 : 2))))
                    .multilineTextAlignment(.trailing)
                    .frame(width: 70)
                if !param.unit.isEmpty {
                    Text(param.unit).foregroundStyle(.secondary)
                }
                Stepper("", value: Binding(get: { value }, set: { model.set(param, .number($0)) }),
                        in: (param.min ?? -1e9)...(param.max ?? 1e9), step: step)
                    .labelsHidden()
            }
        }
    }
}

struct TextParam: View {
    @Environment(AppModel.self) private var model
    let param: Param

    var body: some View {
        let binding = Binding(get: { model.value(param).stringValue ?? "" }, set: { model.set(param, .string($0)) })
        if param.isMultiline {
            VStack(alignment: .leading, spacing: 4) {
                Text(param.label)
                TextEditor(text: Binding(
                    get: { binding.wrappedValue.replacingOccurrences(of: "|", with: "\n") },
                    set: { binding.wrappedValue = $0.replacingOccurrences(of: "\n", with: "|") }))
                    .font(.body)
                    .frame(minHeight: 54, maxHeight: 110)
                    .overlay(RoundedRectangle(cornerRadius: 5).strokeBorder(.separator))
                if !param.help.isEmpty {
                    Text(param.help).font(.caption).foregroundStyle(.secondary)
                }
            }
        } else {
            TextField(param.label, text: binding, prompt: Text(param.help.isEmpty ? "" : param.help))
        }
    }
}

/// Ein Motiv aus der Bibliothek – Raster mit Vorschaubildern.
struct MotivPicker: View {
    @Environment(AppModel.self) private var model
    let param: Param

    var body: some View {
        let current = model.value(param).stringValue ?? ""
        VStack(alignment: .leading, spacing: 6) {
            Text(param.label)
            MotivGrid(selected: [current]) { id in model.set(param, .string(id)) }
        }
    }
}

struct MotivGrid: View {
    @Environment(AppModel.self) private var model
    var selected: Set<String>
    var onPick: (String) -> Void

    var body: some View {
        LazyVGrid(columns: [GridItem(.adaptive(minimum: 58), spacing: 6)], spacing: 6) {
            ForEach(model.schema?.motive ?? []) { m in
                Button { onPick(m.id) } label: {
                    VStack(spacing: 2) {
                        MotivThumb(motiv: m)
                            .frame(width: 44, height: 44)
                        Text(m.name).font(.caption2).lineLimit(1)
                    }
                    .padding(4)
                    .frame(maxWidth: .infinity)
                    .background(selected.contains(m.id) ? Theme.accent.opacity(0.18) : .clear,
                                in: RoundedRectangle(cornerRadius: 6))
                    .overlay(RoundedRectangle(cornerRadius: 6)
                        .strokeBorder(selected.contains(m.id) ? Theme.accent : .clear, lineWidth: 1.5))
                }
                .buttonStyle(.plain)
                .help(m.name)
            }
        }
    }
}

/// Motiv-Umriss aus den normierten Flächen (Löcher per Even-Odd ausgespart).
struct MotivThumb: View {
    let motiv: Motiv

    var body: some View {
        Canvas { ctx, size in
            let s = min(size.width, size.height) * 0.9
            let scale = s / max(motiv.w, motiv.h, 0.001)
            func pt(_ p: Pt) -> CGPoint {
                CGPoint(x: size.width / 2 + p.x * scale, y: size.height / 2 + p.y * scale)
            }
            var fillPath = Path()
            for f in motiv.flaechen {
                for ring in [f.aussen] + f.loecher where ring.count > 2 {
                    fillPath.addLines(ring.map(pt))
                    fillPath.closeSubpath()
                }
            }
            ctx.fill(fillPath, with: .color(.primary), style: FillStyle(eoFill: true))
            var lines = Path()
            for l in motiv.linien where l.count > 1 { lines.addLines(l.map(pt)) }
            ctx.stroke(lines, with: .color(.primary), lineWidth: 1)
        }
    }
}

/// Mehrere platzierte Motive (Typ `motive`): Liste mit Größe/Lage, Hinzufügen aus dem Raster.
struct MotiveList: View {
    @Environment(AppModel.self) private var model
    let param: Param
    @State private var showPicker = false

    private var items: [[String: JSONValue]] {
        (model.value(param).arrayValue ?? []).compactMap(\.objectValue)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(param.label)
                Spacer()
                Button { showPicker.toggle() } label: { Image(systemName: "plus") }
                    .disabled(items.count >= Int(param.max ?? 12))
                    .popover(isPresented: $showPicker) {
                        ScrollView {
                            MotivGrid(selected: []) { id in
                                add(id)
                                showPicker = false
                            }
                            .padding()
                        }
                        .frame(width: 320, height: 300)
                    }
            }
            ForEach(Array(items.enumerated()), id: \.offset) { idx, item in
                MotivRow(param: param, index: idx, item: item, update: { update(idx, $0) }, remove: { remove(idx) })
            }
            if !param.help.isEmpty {
                Text(param.help).font(.caption).foregroundStyle(.secondary)
            }
        }
    }

    private func write(_ list: [[String: JSONValue]]) {
        model.set(param, .array(list.map { .object($0) }))
    }

    private func add(_ id: String) {
        var list = items
        let art = param.arten.first?.value ?? "schnitt"
        list.append(["id": .string(id), "x": 0, "y": 0, "groesse": 40, "drehung": 0, "spiegeln": false, "art": art])
        write(list)
    }

    private func update(_ idx: Int, _ item: [String: JSONValue]) {
        var list = items
        guard list.indices.contains(idx) else { return }
        list[idx] = item
        write(list)
    }

    private func remove(_ idx: Int) {
        var list = items
        guard list.indices.contains(idx) else { return }
        list.remove(at: idx)
        write(list)
    }
}

struct MotivRow: View {
    @Environment(AppModel.self) private var model
    let param: Param
    let index: Int
    let item: [String: JSONValue]
    let update: ([String: JSONValue]) -> Void
    let remove: () -> Void

    var body: some View {
        let id = item["id"]?.stringValue ?? ""
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                if let m = model.schema?.motiv(id: id) {
                    MotivThumb(motiv: m).frame(width: 22, height: 22)
                    Text(m.name)
                } else {
                    Text(id)
                }
                Spacer()
                if !param.arten.isEmpty {
                    Picker("", selection: Binding(
                        get: { item["art"]?.stringValue ?? "" },
                        set: { v in var i = item; i["art"] = .string(v); update(i) })) {
                        ForEach(param.arten) { a in Text(a.label).tag(a.id) }
                    }
                    .labelsHidden()
                    .frame(width: 150)
                }
                Button(role: .destructive, action: remove) { Image(systemName: "trash") }
                    .buttonStyle(.borderless)
            }
            HStack {
                num("x", "x")
                num("y", "y")
                num("groesse", "Größe")
                num("drehung", "°")
            }
        }
        .padding(6)
        .background(.quaternary.opacity(0.4), in: RoundedRectangle(cornerRadius: 6))
    }

    private func num(_ key: String, _ label: String) -> some View {
        HStack(spacing: 2) {
            Text(label).font(.caption).foregroundStyle(.secondary)
            TextField("", value: Binding(
                get: { item[key]?.doubleValue ?? 0 },
                set: { v in var i = item; i[key] = .number(v); update(i) }), format: .number)
                .frame(width: 44)
        }
    }
}
