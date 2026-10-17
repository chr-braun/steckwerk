import XCTest
@testable import SteckwerkCore

final class SchemaParsingTests: XCTestCase {
    func fixture(_ name: String) throws -> Data {
        let url = try XCTUnwrap(Bundle.module.url(forResource: name, withExtension: "json", subdirectory: "Fixtures"))
        return try Data(contentsOf: url)
    }

    func testSchemaModelleUndParameter() throws {
        let s = try Schema.decode(try fixture("schema"))
        XCTAssertFalse(s.version.isEmpty)
        let haus = try XCTUnwrap(s.models["wichtelhaus"])
        XCTAssertEqual(haus.label, "Wichtelhaus")
        XCTAssertEqual(haus.group, "Häuser")
        let width = try XCTUnwrap(haus.params.first { $0.key == "width" })
        XCTAssertEqual(width.type, .number)
        XCTAssertEqual(width.unit, "mm")
        XCTAssertEqual(width.min, 40)
        XCTAssertEqual(width.max, 300)
        XCTAssertEqual(haus.defaults["width"]?.doubleValue, 80)
        XCTAssertEqual(haus.params.first { $0.key == "front_windows" }?.type, .int)
        XCTAssertEqual(haus.params.first { $0.key == "light" }?.type, .bool)
        let door = try XCTUnwrap(haus.params.first { $0.key == "door" })
        XCTAssertEqual(door.type, .select)
        XCTAssertTrue(door.options.contains { $0.id == "arched" })
        XCTAssertEqual(door.section, "Fenster und Tür")
        XCTAssertTrue(haus.sections.contains { $0.title == "Fenster und Tür" })
    }

    func testMotivTypenUndBedingungen() throws {
        let s = try Schema.decode(try fixture("schema"))
        let aufsteller = try XCTUnwrap(s.models["motiv_aufsteller"])
        let motive = try XCTUnwrap(aufsteller.params.first { $0.type == .motive })
        XCTAssertEqual(motive.defaultValue.arrayValue?.first?["id"]?.stringValue, "stern")
        XCTAssertFalse(motive.arten.isEmpty)

        let fahrzeug = try XCTUnwrap(s.models["fahrzeug"])
        let axles = try XCTUnwrap(fahrzeug.params.first { $0.key == "axles" })
        XCTAssertTrue(axles.isVisible(values: ["vehicle": "lkw"]))
        XCTAssertFalse(axles.isVisible(values: ["vehicle": "lok"]))
        XCTAssertFalse(axles.isVisible(values: [:]))
    }

    func testConfigMotivePakete() throws {
        let s = try Schema.decode(try fixture("schema"))
        XCTAssertEqual(s.config.first { $0.key == "thickness" }?.defaultValue.doubleValue, 3.0)
        XCTAssertEqual(s.config.first { $0.key == "cut_color" }?.type, .text)
        let m = try XCTUnwrap(s.motive.first)
        XCTAssertFalse(m.flaechen.isEmpty)
        XCTAssertGreaterThan(m.flaechen[0].aussen.count, 2)
        XCTAssertEqual(s.pakete.first?.id, "wichtel")
        XCTAssertNil(s.pakete.first?.fehler)
        XCTAssertEqual(s.outDir, "/tmp/out")
        XCTAssertEqual(s.orderedGroups.first, "Häuser")
        XCTAssertEqual(s.models(in: "Häuser").first?.key, "wichtelhaus")
    }

    func testWerteBegrenzen() throws {
        let s = try Schema.decode(try fixture("schema"))
        let p = try XCTUnwrap(s.models["wichtelhaus"]?.params.first { $0.key == "front_windows" })
        XCTAssertEqual(p.clamp(9), .number(4))
        XCTAssertEqual(p.clamp(1.6), .number(2))
        let t = try XCTUnwrap(s.models["wichtelhaus"]?.params.first { $0.key == "giebel_text" })
        XCTAssertEqual(t.clamp(.string(String(repeating: "x", count: 50))).stringValue?.count, 24)
    }

    func testGenerateErgebnisUndVorschau() throws {
        let r = try JSONDecoder().decode(GenerateResult.self, from: try fixture("generate_wichtelhaus"))
        XCTAssertTrue(r.ok)
        XCTAssertEqual(r.statusLine, "CUT-READY · 0 FEHLER")
        let a = try XCTUnwrap(r.assemblies.first)
        XCTAssertTrue(a.summary.contains("0 FEHLER"))
        XCTAssertFalse(a.notes.isEmpty)
        XCTAssertTrue(a.reportLines.contains { $0.level == .ok })
        XCTAssertFalse(a.reportLines.contains { $0.level == .fehler })
        let sheet = try XCTUnwrap(a.sheets.first)
        let d = sheet.drawing
        XCTAssertEqual(d.width, 400)
        XCTAssertEqual(d.height, 300)
        XCTAssertEqual(d.paths.count, 278)
        XCTAssertEqual(d.paths.reduce(0) { $0 + $1.closed.filter { $0 }.count }, 43)
        XCTAssertTrue(d.paths.contains { $0.stroke.uppercased() == "#0000FF" })
        XCTAssertTrue(d.paths.contains { SheetDrawing.isCut($0.stroke) })
        let b = try XCTUnwrap(d.bounds)
        XCTAssertGreaterThanOrEqual(b.minX, 0)
        XCTAssertLessThanOrEqual(b.maxX, 400)
    }

    func testFehlerAntwort() throws {
        let json = #"{"ok": false, "error": "Breite: 5 liegt außerhalb 40–300 mm", "assemblies": [], "elapsed": 0.0}"#
        let r = try JSONDecoder().decode(GenerateResult.self, from: Data(json.utf8))
        XCTAssertFalse(r.ok)
        XCTAssertEqual(r.statusLine, "Breite: 5 liegt außerhalb 40–300 mm")
    }
}
