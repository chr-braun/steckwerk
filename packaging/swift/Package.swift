// swift-tools-version:5.9
// Steckwerk Desktop – native macOS-Oberfläche für die Python-Engine (webui.py).
import PackageDescription

let package = Package(
    name: "SteckwerkDesktop",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "SteckwerkDesktop", targets: ["SteckwerkDesktop"]),
    ],
    targets: [
        // Reine Foundation-Logik (Schema, Bridge, SVG-Pfade) – ohne Oberfläche testbar.
        .target(name: "SteckwerkCore"),
        .executableTarget(name: "SteckwerkDesktop", dependencies: ["SteckwerkCore"]),
        .testTarget(name: "SteckwerkDesktopTests", dependencies: ["SteckwerkCore"],
                    resources: [.copy("Fixtures")]),
    ]
)
