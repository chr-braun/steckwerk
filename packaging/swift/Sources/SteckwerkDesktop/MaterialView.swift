import SteckwerkCore
import SwiftUI

/// Material: Stärke T, Kerf, Maßstab, Blattgröße, Farben – aus schema.config, gespeichert pro Mac.
struct MaterialView: View {
    @Environment(AppModel.self) private var model

    private let presets: [(String, Double, Double)] = [
        ("Pappelsperrholz 3 mm", 3.0, 0.2), ("Pappelsperrholz 4 mm", 4.0, 0.2),
        ("MDF 3 mm", 3.0, 0.15), ("Karton 1,5 mm", 1.5, 0.1), ("Acryl 3 mm (CO₂)", 3.0, 0.15),
    ]

    var body: some View {
        Form {
            Section("Schnellwahl") {
                Picker("Material", selection: Binding(get: { -1 }, set: { i in
                    guard presets.indices.contains(i) else { return }
                    model.config["thickness"] = .number(presets[i].1)
                    model.config["kerf"] = .number(presets[i].2)
                    model.saveConfig()
                })) {
                    Text("–").tag(-1)
                    ForEach(presets.indices, id: \.self) { i in Text(presets[i].0).tag(i) }
                }
            }
            Section("Einstellungen") {
                ForEach(model.schema?.config ?? []) { p in
                    ConfigField(param: p)
                }
                Button("Zurücksetzen") {
                    for p in model.schema?.config ?? [] { model.config[p.key] = p.defaultValue }
                    model.saveConfig()
                }
            }
            Section("Ausgabe") {
                LabeledContent("Ordner", value: model.outDir)
                Button("Ordner öffnen") { model.openOutFolder() }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Material")
    }
}

struct ConfigField: View {
    @Environment(AppModel.self) private var model
    let param: Param

    var body: some View {
        let value = model.config[param.key] ?? param.defaultValue
        switch param.type {
        case .number, .int:
            LabeledContent(param.label) {
                HStack(spacing: 6) {
                    TextField("", value: Binding(get: { value.doubleValue ?? 0 },
                                                 set: { set(.number($0)) }), format: .number)
                        .multilineTextAlignment(.trailing)
                        .frame(width: 80)
                    if !param.unit.isEmpty { Text(param.unit).foregroundStyle(.secondary) }
                    Stepper("", value: Binding(get: { value.doubleValue ?? 0 }, set: { set(.number($0)) }),
                            in: (param.min ?? 0)...(param.max ?? 1e6), step: param.step ?? 0.1)
                        .labelsHidden()
                }
            }
            .help(param.help)
        case .select:
            Picker(param.label, selection: Binding(get: { value.stringValue ?? "" }, set: { set(.string($0)) })) {
                ForEach(param.options) { o in Text(o.label).tag(o.id) }
            }
        case .bool:
            Toggle(param.label, isOn: Binding(get: { value.boolValue ?? false }, set: { set(.bool($0)) }))
        default:
            HStack {
                TextField(param.label, text: Binding(get: { value.stringValue ?? "" }, set: { set(.string($0)) }))
                if param.key.hasSuffix("_color"), let c = Color(hex: value.stringValue ?? "") {
                    RoundedRectangle(cornerRadius: 3).fill(c).frame(width: 18, height: 18)
                }
            }
            .help(param.help)
        }
    }

    private func set(_ v: JSONValue) {
        model.config[param.key] = param.clamp(v)
        model.saveConfig()
    }
}

extension Color {
    init?(hex: String) {
        var s = hex.trimmingCharacters(in: .whitespaces)
        if s.hasPrefix("#") { s.removeFirst() }
        guard s.count == 6, let n = UInt32(s, radix: 16) else { return nil }
        self.init(red: Double((n >> 16) & 0xff) / 255, green: Double((n >> 8) & 0xff) / 255,
                  blue: Double(n & 0xff) / 255)
    }
}
