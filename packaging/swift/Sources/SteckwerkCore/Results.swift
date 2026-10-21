import Foundation

/// Antwort von POST /api/generate.
public struct GenerateResult: Decodable, Sendable {
    public var ok: Bool
    public var error: String?
    public var elapsed: Double
    public var assemblies: [Assembly]

    enum CodingKeys: String, CodingKey { case ok, error, elapsed, assemblies }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        error = try c.decodeIfPresent(String.self, forKey: .error)
        elapsed = try c.decodeIfPresent(Double.self, forKey: .elapsed) ?? 0
        assemblies = try c.decodeIfPresent([Assembly].self, forKey: .assemblies) ?? []
    }

    /// Kurzfassung für die Statusanzeige, z. B. „OK · 0 FEHLER“.
    public var statusLine: String {
        if let error { return error }
        let fehler = assemblies.reduce(0) { $0 + $1.errors.count }
        return ok ? "CUT-READY · 0 FEHLER" : "\(fehler) FEHLER"
    }
}

public struct Assembly: Decodable, Sendable, Identifiable {
    public var name: String
    public var ok: Bool
    public var summary: String
    public var report: String
    public var notes: [String]
    public var parts: Int
    public var joints: Int
    public var errors: [String]
    public var sheets: [Sheet]

    public var id: String { name }

    enum CodingKeys: String, CodingKey { case name, ok, summary, report, notes, parts, joints, errors, sheets }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? "modell"
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        summary = try c.decodeIfPresent(String.self, forKey: .summary) ?? ""
        report = try c.decodeIfPresent(String.self, forKey: .report) ?? ""
        notes = try c.decodeIfPresent([String].self, forKey: .notes) ?? []
        parts = try c.decodeIfPresent(Int.self, forKey: .parts) ?? 0
        joints = try c.decodeIfPresent(Int.self, forKey: .joints) ?? 0
        errors = try c.decodeIfPresent([String].self, forKey: .errors) ?? []
        sheets = try c.decodeIfPresent([Sheet].self, forKey: .sheets) ?? []
    }

    /// Prüfbericht zeilenweise mit Status (OK/WARNUNG/FEHLER) für die farbige Anzeige.
    public var reportLines: [ReportLine] {
        report.split(separator: "\n", omittingEmptySubsequences: false).map { ReportLine(text: String($0)) }
    }
}

public struct ReportLine: Sendable, Hashable {
    public enum Level: Sendable { case ok, warnung, fehler, info }
    public var text: String

    public var level: Level {
        let t = text.trimmingCharacters(in: .whitespaces).uppercased()
        if t.hasPrefix("FEHLER") || t.contains(" FEHLER ") && !t.contains("0 FEHLER") { return .fehler }
        if t.hasPrefix("WARN") { return .warnung }
        if t.hasPrefix("OK") || t.contains("CUT-READY") { return .ok }
        return .info
    }
}

public struct Sheet: Decodable, Sendable, Identifiable {
    public var file: String
    public var svg: String
    public var width: Double
    public var height: Double
    public var parts: Int
    public var checked: Bool

    public var id: String { file }

    enum CodingKeys: String, CodingKey { case file, svg, width, height, parts, checked }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        file = try c.decodeIfPresent(String.self, forKey: .file) ?? "blatt.svg"
        svg = try c.decodeIfPresent(String.self, forKey: .svg) ?? ""
        width = try c.decodeIfPresent(Double.self, forKey: .width) ?? 0
        height = try c.decodeIfPresent(Double.self, forKey: .height) ?? 0
        parts = try c.decodeIfPresent(Int.self, forKey: .parts) ?? 0
        checked = try c.decodeIfPresent(Bool.self, forKey: .checked) ?? false
    }

    /// Geometrie für die native Vorschau.
    public var drawing: SheetDrawing { SheetDrawing(svg: svg, width: width, height: height) }
}
