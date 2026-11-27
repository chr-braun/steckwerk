import Foundation
import XCTest
@testable import SteckwerkCore

final class WiederaufnahmeTests: XCTestCase {
    private func frischeDefaults() -> UserDefaults {
        let name = "steckwerk-test-\(UUID().uuidString)"
        let d = UserDefaults(suiteName: name)!
        d.removePersistentDomain(forName: name)
        return d
    }

    func testSichernUndNehmenGenauEinmal() {
        let d = frischeDefaults()
        let w = Wiederaufnahme(auswahl: "model:wichtelhaus",
                               werte: ["wichtelhaus": ["width": .double(120), "name": .string("Anna")]],
                               projekt: "Omas Haus", projektGeaendert: true, blatt: 2)
        w.sichern(in: d)
        let zurueck = Wiederaufnahme.nehmen(aus: d)
        XCTAssertEqual(zurueck?.auswahl, "model:wichtelhaus")
        XCTAssertEqual(zurueck?.werte["wichtelhaus"]?["name"], .string("Anna"))
        XCTAssertEqual(zurueck?.projekt, "Omas Haus")
        XCTAssertEqual(zurueck?.projektGeaendert, true)
        XCTAssertEqual(zurueck?.blatt, 2)
        XCTAssertNil(Wiederaufnahme.nehmen(aus: d), "nur der erste Start nach dem Update übernimmt den Zustand")
    }

    func testAlterZustandWirdVerworfen() {
        let d = frischeDefaults()
        Wiederaufnahme(auswahl: "alle", werte: [:], gesichert: Date(timeIntervalSinceNow: -3600)).sichern(in: d)
        XCTAssertNil(Wiederaufnahme.nehmen(aus: d))
        XCTAssertNil(d.data(forKey: Wiederaufnahme.defaultsKey))
    }

    func testOhneEintragNil() {
        XCTAssertNil(Wiederaufnahme.nehmen(aus: frischeDefaults()))
    }
}
