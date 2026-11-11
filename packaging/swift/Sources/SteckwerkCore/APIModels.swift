import Foundation

public struct PingResponse: Decodable, Sendable {
    public let ok: Bool
    public let app: String?
    public let version: String?

    enum CodingKeys: String, CodingKey { case ok, app, version }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        app = try c.decodeIfPresent(String.self, forKey: .app)
        version = try c.decodeIfPresent(String.self, forKey: .version)
    }
}

/// Antwort von POST /api/generate.
public struct GenerateResponse: Decodable, Sendable {
    public let ok: Bool
    public let error: String?
    public let assemblies: [Assembly]

    enum CodingKeys: String, CodingKey { case ok, error, assemblies }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        error = try c.decodeIfPresent(String.self, forKey: .error)
        assemblies = try c.decodeIfPresent([Assembly].self, forKey: .assemblies) ?? []
    }

    public var errorCount: Int {
        assemblies.reduce(0) { $0 + $1.errors.count }
    }

    /// Exportieren ist nur erlaubt, wenn der Validator alles als CUT-READY bestätigt hat.
    public var canExport: Bool {
        ok && !assemblies.isEmpty && assemblies.allSatisfy { $0.ok && !$0.sheets.isEmpty }
    }
}

public struct Assembly: Decodable, Sendable, Identifiable {
    public var id: String { name }
    public let name: String
    public let ok: Bool
    public let summary: String
    public let report: String
    public let notes: [String]
    public let parts: Int
    public let joints: Int
    public let errors: [String]
    public let sheets: [SheetResult]
    /// Laserzeit, Schnittlänge und Plattenbedarf (Schätzung der Engine, ab 2.11).
    public let schaetzung: Schaetzung?
    /// Teileliste mit Nummer, Größe und Prüfergebnis – für den Prüfbericht und die Auswahl „Auf Teil“ der Gravur.
    public let teile: [TeilInfo]

    enum CodingKeys: String, CodingKey { case name, ok, summary, report, notes, parts, joints, errors, sheets, schaetzung, teile }

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
        sheets = try c.decodeIfPresent([SheetResult].self, forKey: .sheets) ?? []
        schaetzung = try? c.decodeIfPresent(Schaetzung.self, forKey: .schaetzung)
        teile = (try? c.decodeIfPresent([TeilInfo].self, forKey: .teile)) ?? []
    }

    /// Montagehinweis ohne das vorangestellte „modell: “.
    public func hinweis(_ note: String) -> String {
        let prefix = name + ":"
        guard note.hasPrefix(prefix) else { return note }
        return String(note.dropFirst(prefix.count)).trimmingCharacters(in: .whitespaces)
    }
}

/// Ein Teil im Prüfbericht: Nummer wie bei „Teilenummern gravieren“, Name, Außenmaße, geprüft.
public struct TeilInfo: Decodable, Sendable, Identifiable, Hashable {
    public var id: Int { nr }
    public let nr: Int
    public let name: String
    public let w: Double
    public let h: Double
    public let ok: Bool

    enum CodingKeys: String, CodingKey { case nr, name, w, h, ok }

    public init(nr: Int, name: String, w: Double, h: Double, ok: Bool) {
        self.nr = nr; self.name = name; self.w = w; self.h = h; self.ok = ok
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        nr = try c.decodeIfPresent(Int.self, forKey: .nr) ?? 0
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? ""
        w = try c.decodeIfPresent(Double.self, forKey: .w) ?? 0
        h = try c.decodeIfPresent(Double.self, forKey: .h) ?? 0
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? true
    }

    /// „wichtelhaus_dach_links“ in der Baugruppe „wichtelhaus“ → „Dach links“
    public func anzeigeName(baugruppe: String) -> String {
        var s = name.hasPrefix(baugruppe + "_") ? String(name.dropFirst(baugruppe.count + 1)) : name
        s = s.replacingOccurrences(of: "_", with: " ").trimmingCharacters(in: .whitespaces)
        guard let first = s.first else { return name }
        return first.uppercased() + s.dropFirst()
    }

    /// „79,8 × 63,4 mm“
    public var groesse: String {
        func de(_ v: Double) -> String { String(format: "%g", v).replacingOccurrences(of: ".", with: ",") }
        return "\(de(w)) × \(de(h)) mm"
    }
}

/// Ein gespeichertes Projekt (~/.steckwerk/projekte.json, gemeinsam mit der Browser-Oberfläche).
public struct Projekt: Decodable, Sendable, Identifiable, Hashable {
    public var id: String { name }
    public let name: String
    public let model: String
    public let params: [String: JSONValue]
    public let config: [String: JSONValue]
    public let geaendert: Double

    enum CodingKeys: String, CodingKey { case name, model, params, config, geaendert }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? ""
        model = try c.decodeIfPresent(String.self, forKey: .model) ?? ""
        params = (try? c.decodeIfPresent([String: JSONValue].self, forKey: .params)) ?? [:]
        config = (try? c.decodeIfPresent([String: JSONValue].self, forKey: .config)) ?? [:]
        geaendert = try c.decodeIfPresent(Double.self, forKey: .geaendert) ?? 0
    }
}

/// Antwort von POST /api/projekte.
public struct ProjekteResponse: Decodable, Sendable {
    public let ok: Bool
    public let error: String?
    public let projekte: [Projekt]

    enum CodingKeys: String, CodingKey { case ok, error, projekte }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        error = try c.decodeIfPresent(String.self, forKey: .error)
        projekte = (try? c.decodeIfPresent([Projekt].self, forKey: .projekte)) ?? []
    }
}

/// Schätzung für ein Modell: Laserzeit, Schnitt- und Ritzlänge, Platten und (mit Preis) Materialkosten.
public struct Schaetzung: Decodable, Sendable {
    public let zeit: String
    public let sekunden: Double
    public let schnittM: Double
    public let ritzM: Double
    public let platten: Double
    public let ausnutzung: Int
    public let kosten: Double?

    enum CodingKeys: String, CodingKey { case zeit, sekunden, platten, ausnutzung, kosten
        case schnittM = "schnitt_m", ritzM = "ritz_m"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        zeit = try c.decodeIfPresent(String.self, forKey: .zeit) ?? ""
        sekunden = try c.decodeIfPresent(Double.self, forKey: .sekunden) ?? 0
        schnittM = try c.decodeIfPresent(Double.self, forKey: .schnittM) ?? 0
        ritzM = try c.decodeIfPresent(Double.self, forKey: .ritzM) ?? 0
        platten = try c.decodeIfPresent(Double.self, forKey: .platten) ?? 0
        ausnutzung = try c.decodeIfPresent(Int.self, forKey: .ausnutzung) ?? 0
        kosten = try c.decodeIfPresent(Double.self, forKey: .kosten)
    }

    /// „Laserzeit ca. 15 min · 2,7 m Schnitt · 0,3 Platten“
    public var text: String {
        func de(_ v: Double) -> String { String(format: "%g", v).replacingOccurrences(of: ".", with: ",") }
        var t = "Laserzeit ca. \(zeit) · \(de(schnittM)) m Schnitt"
        if ritzM > 0 { t += " · \(de(ritzM)) m Ritzen" }
        t += " · \(de(platten)) \(platten == 1 ? "Platte" : "Platten")"
        if let kosten { t += String(format: " · ca. %.2f €", kosten).replacingOccurrences(of: ".", with: ",") }
        return t
    }
}

/// Antwort von POST /api/xcs-oeffnen.
public struct XcsOeffnenResponse: Decodable, Sendable {
    public let ok: Bool
    public let message: String?
    public let error: String?
    public let datei: String?

    enum CodingKeys: String, CodingKey { case ok, message, error, datei }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        message = try c.decodeIfPresent(String.self, forKey: .message)
        error = try c.decodeIfPresent(String.self, forKey: .error)
        datei = try c.decodeIfPresent(String.self, forKey: .datei)
    }
}

public struct SheetResult: Decodable, Sendable, Identifiable {
    public var id: String { file }
    public let file: String
    public let svg: String
    public let width: Double
    public let height: Double
    public let parts: Int
    public let checked: Bool

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
}

public struct SaveResponse: Decodable, Sendable {
    public let ok: Bool
    public let outDir: String?
    public let files: [String]

    enum CodingKeys: String, CodingKey { case ok, files
        case outDir = "out_dir"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        outDir = try c.decodeIfPresent(String.self, forKey: .outDir)
        files = try c.decodeIfPresent([String].self, forKey: .files) ?? []
    }
}

/// Antworten mit Meldung und ggf. neuem Schema (Pakete installieren/entfernen, Kanal-Pakete).
public struct MessageResponse: Decodable, Sendable {
    public let ok: Bool
    public let message: String?
    public let schema: Schema?

    enum CodingKeys: String, CodingKey { case ok, message, schema }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        message = try c.decodeIfPresent(String.self, forKey: .message)
        schema = try? c.decodeIfPresent(Schema.self, forKey: .schema)
    }
}

/// Antwort von POST /api/desktop-check: Stand der „Steckwerk Desktop.app“ im Update-Kanal.
public struct DesktopCheck: Decodable, Sendable {
    public let installiert: String
    public let version: String
    public let neu: Bool
    public let hinweise: [String]
    public let kannInstallieren: Bool
    public let grund: String

    enum CodingKeys: String, CodingKey {
        case installiert, version, neu, hinweise, grund
        case kannInstallieren = "kann_installieren"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        installiert = (try? c.decodeIfPresent(String.self, forKey: .installiert)) ?? ""
        version = (try? c.decodeIfPresent(String.self, forKey: .version)) ?? ""
        neu = (try? c.decodeIfPresent(Bool.self, forKey: .neu)) ?? false
        hinweise = (try? c.decodeIfPresent([String].self, forKey: .hinweise)) ?? []
        kannInstallieren = (try? c.decodeIfPresent(Bool.self, forKey: .kannInstallieren)) ?? false
        grund = (try? c.decodeIfPresent(String.self, forKey: .grund)) ?? ""
    }
}

/// Antwort von POST /api/desktop-install: neue App liegt am alten Ort und will neu gestartet werden.
public struct DesktopUpdateResponse: Decodable, Sendable {
    public let version: String
    public let pfad: String
    public let message: String?
}

/// Antwort von POST /api/update-check.
public struct UpdateCheck: Decodable, Sendable {
    public let programm: ProgrammInfo
    public let pakete: [KanalPaket]
    public let updates: Int

    enum CodingKeys: String, CodingKey { case programm, pakete, updates }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        programm = try c.decode(ProgrammInfo.self, forKey: .programm)
        pakete = try c.decodeIfPresent([KanalPaket].self, forKey: .pakete) ?? []
        updates = try c.decodeIfPresent(Int.self, forKey: .updates) ?? 0
    }

    /// Kanalpakete nach Bereich gruppiert, in der Reihenfolge des Kanals; ältere Kanäle ohne Bereiche geben eine Gruppe ohne Namen.
    public var bereiche: [(name: String, pakete: [KanalPaket])] {
        var gruppen: [(name: String, pakete: [KanalPaket])] = []
        for paket in pakete {
            if let i = gruppen.firstIndex(where: { $0.name == paket.bereichName }) {
                gruppen[i].pakete.append(paket)
            } else {
                gruppen.append((paket.bereichName, [paket]))
            }
        }
        return gruppen
    }
}

public struct ProgrammInfo: Decodable, Sendable {
    public let installiert: String
    public let version: String
    public let neu: Bool
    public let datum: String
    public let hinweise: [String]
    public let grund: String
    /// Die Engine kann diese App selbst ersetzen (Kanal hat ein passendes Paket, Ort ist beschreibbar).
    public let kannInstallieren: Bool

    enum CodingKeys: String, CodingKey {
        case installiert, version, neu, datum, hinweise, grund
        case kannInstallieren = "kann_installieren"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        installiert = try c.decodeIfPresent(String.self, forKey: .installiert) ?? ""
        version = try c.decodeIfPresent(String.self, forKey: .version) ?? ""
        neu = try c.decodeIfPresent(Bool.self, forKey: .neu) ?? false
        datum = try c.decodeIfPresent(String.self, forKey: .datum) ?? ""
        hinweise = try c.decodeIfPresent([String].self, forKey: .hinweise) ?? []
        grund = (try? c.decodeIfPresent(String.self, forKey: .grund)) ?? ""
        kannInstallieren = (try? c.decodeIfPresent(Bool.self, forKey: .kannInstallieren)) ?? false
    }
}

public struct KanalPaket: Decodable, Sendable, Identifiable {
    public let id: String
    public let name: String
    public let version: String
    public let beschreibung: String
    public let installiert: String?
    public let status: String
    public let benoetigt: [String]
    public let groesse: Int
    /// Bereich im Paketkatalog (Kanal ab 2.13.0), z. B. „feste“; leer bei älteren Kanälen.
    public let bereich: String
    public let bereichName: String

    enum CodingKeys: String, CodingKey {
        case id, name, version, beschreibung, installiert, status, benoetigt, groesse, bereich
        case bereichName = "bereich_name"
    }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        id = try c.decode(String.self, forKey: .id)
        name = try c.decodeIfPresent(String.self, forKey: .name) ?? id
        version = try c.decodeIfPresent(String.self, forKey: .version) ?? ""
        beschreibung = try c.decodeIfPresent(String.self, forKey: .beschreibung) ?? ""
        installiert = try? c.decodeIfPresent(String.self, forKey: .installiert)
        status = try c.decodeIfPresent(String.self, forKey: .status) ?? ""
        benoetigt = (try? c.decodeIfPresent([String].self, forKey: .benoetigt)) ?? []
        groesse = (try? c.decodeIfPresent(Int.self, forKey: .groesse)) ?? 0
        bereich = (try? c.decodeIfPresent(String.self, forKey: .bereich)) ?? ""
        bereichName = (try? c.decodeIfPresent(String.self, forKey: .bereichName)) ?? ""
    }

    /// Installierbar, wenn noch nicht installiert oder eine neuere Version im Kanal liegt.
    public var installable: Bool {
        guard let installiert, !installiert.isEmpty else { return true }
        return installiert != version
    }
}

/// Antwort von POST /api/assistent-status.
public struct AssistentStatus: Decodable, Sendable {
    public let ok: Bool
    public let error: String?
    public let modelle: [String]

    enum CodingKeys: String, CodingKey { case ok, error, modelle }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        error = try c.decodeIfPresent(String.self, forKey: .error)
        modelle = (try? c.decodeIfPresent([String].self, forKey: .modelle)) ?? []
    }
}

/// Antwort von POST /api/assistent: geprüfte Werte für das gewählte Modell.
public struct AssistentVorschlag: Decodable, Sendable {
    public let werte: [String: JSONValue]
    public let hinweis: String
    public let verworfen: [String]

    enum CodingKeys: String, CodingKey { case werte, hinweis, verworfen }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        werte = try c.decodeIfPresent([String: JSONValue].self, forKey: .werte) ?? [:]
        hinweis = try c.decodeIfPresent(String.self, forKey: .hinweis) ?? ""
        let raw = (try? c.decodeIfPresent([JSONValue].self, forKey: .verworfen)) ?? []
        verworfen = raw.map(\.displayText)
    }
}

/// Antwort von POST /api/bild.
public struct BildErgebnis: Decodable, Sendable {
    public let bild: String
    public let typ: String
    public let quelle: String
    public let modell: String
    public let kosten: Double

    enum CodingKeys: String, CodingKey { case bild, typ, quelle, modell, kosten }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        bild = try c.decode(String.self, forKey: .bild)
        typ = try c.decodeIfPresent(String.self, forKey: .typ) ?? "image/png"
        quelle = try c.decodeIfPresent(String.self, forKey: .quelle) ?? ""
        modell = try c.decodeIfPresent(String.self, forKey: .modell) ?? ""
        kosten = try c.decodeIfPresent(Double.self, forKey: .kosten) ?? 0
    }

    public var data: Data? { Data(base64Encoded: bild) }

    public var dateiendung: String {
        switch typ {
        case "image/svg+xml": return "svg"
        case "image/jpeg": return "jpg"
        case "image/webp": return "webp"
        default: return "png"
        }
    }
}

/// Antwort von POST /api/motiv-import und /api/motiv-entfernen.
public struct MotivResponse: Decodable, Sendable {
    public let ok: Bool
    public let message: String?
    public let id: String?
}

public struct FotoResponse: Decodable, Sendable {
    public let ok: Bool
    public let message: String?
    public let error: String?
    public let id: String?
    public let bilder: [BildInfo]

    enum CodingKeys: String, CodingKey { case ok, message, error, id, bilder }

    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        ok = try c.decodeIfPresent(Bool.self, forKey: .ok) ?? false
        message = try c.decodeIfPresent(String.self, forKey: .message)
        error = try c.decodeIfPresent(String.self, forKey: .error)
        id = try c.decodeIfPresent(String.self, forKey: .id)
        bilder = (try? c.decodeIfPresent([BildInfo].self, forKey: .bilder)) ?? []
    }
}
