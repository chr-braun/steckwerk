import Foundation

/// Antwort von GET /api/schema – Modelle, Parameter, Material, Motive, Pakete.
public struct Schema: Decodable, Sendable {
    public var version: String
    public var groups: [String]
    public var groupLabels: [String: String]
    public var models: [String: ModelInfo]
    public var config: [Param]
    public var motive: [Motiv]
    public var pakete: [Paket]
    public var outDir: String?
    public var app: Bool
    public var assistent: JSONValue?
    public var updates: JSONValue?

    enum CodingKeys: String, CodingKey {
        case version, groups, models, config, motive, pakete, app, assistent, updates
        case groupLabels = "group_labels"
        case outDir = "out_dir"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        version = try c.decodeIfPresent(String.self, forKey: .version) ?? ""
        groups = try c.decodeIfPresent([String].self, forKey: .groups) ?? []
        groupLabels = try c.decodeIfPresent([String: String].self, forKey: .groupLabels) ?? [:]
        models = try c.decodeIfPresent([String: ModelInfo].self, forKey: .models) ?? [:]
        config = try c.decodeIfPresent([Param].self, forKey: .config) ?? []
        motive = try c.decodeIfPresent([Motiv].self, forKey: .motive) ?? []
        pakete = try c.decodeIfPresent([Paket].self, forKey: .pakete) ?? []
        outDir = try c.decodeIfPresent(String.self, forKey: .outDir)
        app = try c.decodeIfPresent(Bool.self, forKey: .app) ?? false
        assistent = try c.decodeIfPresent(JSONValue.self, forKey: .assistent)
        updates = try c.decodeIfPresent(JSONValue.self, forKey: .updates)
    }

    public static func decode(_ data: Data) throws -> Schema {
        try JSONDecoder().decode(Schema.self, from: data)
    }

    /// Modelle einer Gruppe, nach Namen sortiert (JSON-Objekte haben in Swift keine feste Reihenfolge).
    public func models(in group: String) -> [(key: String, info: ModelInfo)] {
        models.filter { $0.value.group == group }
            .map { (key: $0.key, info: $0.value) }
            .sorted { $0.info.label.localizedStandardCompare($1.info.label) == .orderedAscending }
    }

    /// Gruppen in der Reihenfolge der Engine, ergänzt um Gruppen, die nur in Modellen vorkommen.
    public var orderedGroups: [String] {
        var out = groups
        for g in Set(models.values.map(\.group)).sorted() where !out.contains(g) {
            out.append(g)
        }
        return out.filter { g in models.values.contains { $0.group == g } }
    }

    public func label(forGroup group: String) -> String {
        groupLabels[group] ?? group
    }

    public func motiv(id: String) -> Motiv? {
        motive.first { $0.id == id }
    }
}

public struct ModelInfo: Decodable, Sendable, Hashable {
    public var label: String
    public var group: String
    public var desc: String
    public var params: [Param]
    public var paketID: String?

    enum CodingKeys: String, CodingKey { case label, group, desc, params, paket }
    enum PaketKeys: String, CodingKey { case id }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        label = try c.decodeIfPresent(String.self, forKey: .label) ?? ""
        group = try c.decodeIfPresent(String.self, forKey: .group) ?? "Weitere"
        desc = try c.decodeIfPresent(String.self, forKey: .desc) ?? ""
        params = try c.decodeIfPresent([Param].self, forKey: .params) ?? []
        if let p = try? c.nestedContainer(keyedBy: PaketKeys.self, forKey: .paket) {
            paketID = try p.decodeIfPresent(String.self, forKey: .id)
        }
    }

    /// Standardwerte aller Parameter – Ausgangspunkt für das Formular.
    public var defaults: [String: JSONValue] {
        Dictionary(params.map { ($0.key, $0.defaultValue) }, uniquingKeysWith: { a, _ in a })
    }

    /// Abschnitte in Reihenfolge des ersten Auftretens; Parameter ohne Abschnitt kommen unter "".
    public var sections: [(title: String, params: [Param])] {
        var order: [String] = []
        var map: [String: [Param]] = [:]
        for p in params {
            let s = p.section ?? ""
            if map[s] == nil { order.append(s) }
            map[s, default: []].append(p)
        }
        return order.map { (title: $0, params: map[$0] ?? []) }
    }
}

public enum ParamType: String, Sendable, Hashable {
    case number, int, select, text, bool, motiv, motive, unknown

    init(raw: String) {
        switch raw {
        case "num", "number", "float": self = .number
        case "int", "integer": self = .int
        case "flag", "bool", "boolean": self = .bool
        default: self = ParamType(rawValue: raw) ?? .unknown
        }
    }
}

public struct ParamOption: Decodable, Sendable, Hashable, Identifiable {
    public var value: JSONValue
    public var label: String
    public var id: String { value.stringValue ?? label }

    enum CodingKeys: String, CodingKey { case value, label }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        value = try c.decodeIfPresent(JSONValue.self, forKey: .value) ?? .null
        label = try c.decodeIfPresent(String.self, forKey: .label) ?? (value.stringValue ?? "")
    }
}

public struct Param: Decodable, Sendable, Hashable, Identifiable {
    public var key: String
    public var label: String
    public var type: ParamType
    public var rawType: String
    public var defaultValue: JSONValue
    public var options: [ParamOption]
    public var min: Double?
    public var max: Double?
    public var step: Double?
    public var unit: String
    public var help: String
    public var section: String?
    public var maxlength: Int?
    public var symbols: Bool
    public var when: [String: [JSONValue]]
    public var arten: [ParamOption]

    public var id: String { key }

    enum CodingKeys: String, CodingKey {
        case key, label, type, options, min, max, step, unit, help, section, maxlength, symbols, when, arten
        case defaultValue = "default"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        key = try c.decode(String.self, forKey: .key)
        label = try c.decodeIfPresent(String.self, forKey: .label) ?? key
        rawType = try c.decodeIfPresent(String.self, forKey: .type) ?? "text"
        type = ParamType(raw: rawType)
        defaultValue = try c.decodeIfPresent(JSONValue.self, forKey: .defaultValue) ?? .null
        options = try c.decodeIfPresent([ParamOption].self, forKey: .options) ?? []
        min = try c.decodeIfPresent(JSONValue.self, forKey: .min)?.doubleValue
        max = try c.decodeIfPresent(JSONValue.self, forKey: .max)?.doubleValue
        step = try c.decodeIfPresent(JSONValue.self, forKey: .step)?.doubleValue
        unit = try c.decodeIfPresent(String.self, forKey: .unit) ?? ""
        help = try c.decodeIfPresent(String.self, forKey: .help) ?? ""
        section = try c.decodeIfPresent(String.self, forKey: .section)
        maxlength = try c.decodeIfPresent(JSONValue.self, forKey: .maxlength)?.doubleValue.map { Int($0) }
        symbols = try c.decodeIfPresent(Bool.self, forKey: .symbols) ?? false
        let w = try c.decodeIfPresent([String: JSONValue].self, forKey: .when) ?? [:]
        when = w.mapValues { $0.arrayValue ?? [$0] }
        arten = try c.decodeIfPresent([ParamOption].self, forKey: .arten) ?? []
    }

    /// Mehrzeiliges Textfeld? Die Engine nimmt „|“ als Zeilenumbruch; lange Felder bekommen einen Editor.
    public var isMultiline: Bool {
        type == .text && ((maxlength ?? 0) > 60 || help.contains("| = neue Zeile"))
    }

    /// Sichtbar unter den aktuellen Werten? (`when`: alle genannten Felder müssen einen der Werte haben.)
    public func isVisible(values: [String: JSONValue]) -> Bool {
        for (other, allowed) in when {
            guard let v = values[other] else { return false }
            let s = v.stringValue
            if !allowed.contains(where: { $0 == v || ($0.stringValue != nil && $0.stringValue == s) }) {
                return false
            }
        }
        return true
    }

    /// Wert auf den erlaubten Bereich bringen (Zahlen) bzw. kürzen (Text).
    public func clamp(_ value: JSONValue) -> JSONValue {
        switch type {
        case .number, .int:
            guard var d = value.doubleValue else { return defaultValue }
            if let lo = min { d = Swift.max(lo, d) }
            if let hi = max { d = Swift.min(hi, d) }
            return .number(type == .int ? d.rounded() : d)
        case .text:
            guard let s = value.stringValue else { return defaultValue }
            if let n = maxlength, s.count > n { return .string(String(s.prefix(n))) }
            return .string(s)
        default:
            return value
        }
    }
}

public struct Motiv: Decodable, Sendable, Hashable, Identifiable {
    public var id: String
    public var name: String
    public var quelle: String
    public var eingebaut: Bool
    public var w: Double
    public var h: Double
    /// Flächen (Außenkontur + Löcher) und Linien in normierten Koordinaten um (0, 0).
    public var flaechen: [Flaeche]
    public var linien: [[Pt]]

    public struct Flaeche: Decodable, Sendable, Hashable {
        public var aussen: [Pt]
        public var loecher: [[Pt]]

        enum CodingKeys: String, CodingKey { case aussen, loecher }

        public init(from decoder: Decoder) throws {
            let c = try decoder.container(keyedBy: CodingKeys.self)
            aussen = Pt.list(try c.decodeIfPresent([[Double]].self, forKey: .aussen) ?? [])
            loecher = (try c.decodeIfPresent([[[Double]]].self, forKey: .loecher) ?? []).map(Pt.list)
        }
    }

    enum CodingKeys: String, CodingKey { case id, name, quelle, eingebaut, w, h, flaechen, linien }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? id
        quelle = try c.decodeIfPresent(String.self, forKey: .quelle) ?? ""
        eingebaut = try c.decodeIfPresent(Bool.self, forKey: .eingebaut) ?? false
        w = try c.decodeIfPresent(Double.self, forKey: .w) ?? 1
        h = try c.decodeIfPresent(Double.self, forKey: .h) ?? 1
        flaechen = (try? c.decodeIfPresent([Flaeche].self, forKey: .flaechen)) ?? []
        linien = ((try? c.decodeIfPresent([[[Double]]].self, forKey: .linien)) ?? []).map(Pt.list)
    }
}

public struct Paket: Decodable, Sendable, Hashable, Identifiable {
    public var id: String
    public var name: String
    public var version: String
    public var autor: String
    public var beschreibung: String
    public var modelle: [String]
    public var fehler: String?

    enum CodingKeys: String, CodingKey { case id, name, version, autor, beschreibung, modelle, fehler }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decodeIfPresent(String.self, forKey: .id) ?? ""
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? id
        version = try c.decodeIfPresent(JSONValue.self, forKey: .version)?.stringValue ?? ""
        autor = try c.decodeIfPresent(String.self, forKey: .autor) ?? ""
        beschreibung = try c.decodeIfPresent(String.self, forKey: .beschreibung) ?? ""
        modelle = try c.decodeIfPresent([String].self, forKey: .modelle) ?? []
        fehler = try c.decodeIfPresent(JSONValue.self, forKey: .fehler)?.stringValue
    }
}

/// Punkt in Millimetern (Blatt) oder normierten Einheiten (Motive).
public struct Pt: Sendable, Hashable {
    public var x: Double
    public var y: Double

    public init(_ x: Double, _ y: Double) {
        self.x = x
        self.y = y
    }

    static func list(_ raw: [[Double]]) -> [Pt] {
        raw.compactMap { $0.count >= 2 ? Pt($0[0], $0[1]) : nil }
    }
}
