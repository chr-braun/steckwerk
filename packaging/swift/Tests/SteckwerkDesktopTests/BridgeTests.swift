import XCTest
@testable import SteckwerkCore

final class BridgeTests: XCTestCase {
    func testURLs() {
        let b = Bridge(port: 8799, client: "test")
        XCTAssertEqual(b.url("/api/schema").absoluteString, "http://127.0.0.1:8799/api/schema")
        XCTAssertEqual(b.url("api/ping").absoluteString, "http://127.0.0.1:8799/api/ping")
        XCTAssertEqual(b.url("/api/schema", lang: "en").absoluteString, "http://127.0.0.1:8799/api/schema?lang=en")
    }

    func testPostHatSchutzHeaderUndClient() throws {
        let b = Bridge(port: 8799, client: "test")
        let req = BuildRequest(model: "wichtelhaus", params: ["width": 90, "door": "rect"], config: ["thickness": 3])
        let r = try b.postRequest("/api/generate", body: req.body)
        XCTAssertEqual(r.httpMethod, "POST")
        XCTAssertEqual(r.value(forHTTPHeaderField: "X-Steckwerk"), "1")
        XCTAssertEqual(r.value(forHTTPHeaderField: "Content-Type"), "application/json")
        let body = try JSONDecoder().decode(JSONValue.self, from: try XCTUnwrap(r.httpBody))
        XCTAssertEqual(body["model"], "wichtelhaus")
        XCTAssertEqual(body["client"], "test")
        XCTAssertEqual(body["params"]?["width"]?.doubleValue, 90)
        XCTAssertEqual(body["params"]?["door"], "rect")
        XCTAssertEqual(body["config"]?["thickness"]?.doubleValue, 3)
    }

    func testGanzzahlenBleibenGanzzahlen() throws {
        let data = try JSONEncoder().encode(JSONValue.object(["n": 2, "f": 2.5]))
        let s = String(decoding: data, as: UTF8.self)
        XCTAssertTrue(s.contains("\"n\":2") && !s.contains("2.0"), s)
        XCTAssertTrue(s.contains("2.5"))
    }

    func testPortZeile() {
        XCTAssertEqual(EnginePort.parse("STECKWERK_PORT=51234"), 51234)
        XCTAssertEqual(EnginePort.parse("  STECKWERK_PORT=8765\r"), 8765)
        XCTAssertNil(EnginePort.parse("Steckwerk läuft"))
        XCTAssertNil(EnginePort.parse("STECKWERK_PORT=99999"))
    }

    func testPfadDaten() {
        let (subs, closed) = SheetDrawing.parseD("M0,0 L10,0 L10,5 Z M20,20 l5,0 v5 h-5")
        XCTAssertEqual(subs.count, 2)
        XCTAssertEqual(closed, [true, false])
        XCTAssertEqual(subs[1].last, Pt(20, 25))
        let (neg, _) = SheetDrawing.parseD("M1e1,-2-3,4")
        XCTAssertEqual(neg.first, [Pt(10, -2), Pt(-3, 4)])
    }

    func testEbenenFarbeWirdVererbt() {
        let svg = """
        <svg viewBox="0 0 100 50"><g stroke="#0000FF" fill="none"><path d="M0,0 L1,1"/></g>\
        <g stroke="#000000"><path stroke="#FF0000" d="M2,2 L3,3"/><path d="M4,4 L5,5"/></g></svg>
        """
        let d = SheetDrawing(svg: svg)
        XCTAssertEqual(d.width, 100)
        XCTAssertEqual(d.height, 50)
        XCTAssertEqual(d.paths.map(\.stroke), ["#0000FF", "#FF0000", "#000000"])
        XCTAssertNil(d.paths[0].fill)
    }

    func testPythonKandidaten() {
        let c = Engine.pythonCandidates(environment: ["STECKWERK_PYTHON": "/x/python3", "HOME": "/Users/t"])
        XCTAssertEqual(c.first, "/x/python3")
        XCTAssertEqual(c[1], "/opt/homebrew/bin/python3")
        XCTAssertTrue(c.contains("/Users/t/.pyenv/shims/python3"))
    }

    func testEngineOrdnerKandidaten() {
        let exe = URL(fileURLWithPath: "/repo/packaging/swift/.build/debug/SteckwerkDesktop")
        let c = Engine.engineDirCandidates(bundleResources: URL(fileURLWithPath: "/App.app/Contents/Resources"),
                                           executable: exe, environment: [:])
        XCTAssertEqual(c.first?.path, "/App.app/Contents/Resources/steckwerk")
        XCTAssertTrue(c.contains { $0.path == "/repo" })
    }
}
