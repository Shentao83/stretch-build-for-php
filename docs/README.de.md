# Build-Rezept für PHP 7.4.33 auf Debian 9

Dieses Repository dokumentiert einen privaten CLI-/FPM-Build auf Debian 9
(Stretch, amd64) mit dem bereits von PHP upstream veröffentlichten Fix für
CVE-2026-109618 und CVE-2026-109619. Der Patch stammt von Arnaud Le Blanc
und Ilija Tovilo; unser Beitrag ist das Build-Rezept samt Prüfungen und Dokumentation.

**Status: experimentelles Quellpaket.** Der hier zusammengefasste Ablauf wurde
am 29. Oktober 2026 unter Debian 9.13 amd64 mit Python 3.5.3 neu gebaut.
Alle sechs PECL-Module sowie die synthetischen CLI- und FPM-Prüfungen waren
erfolgreich. Vollständige Upstream- und Anwendungstests stehen weiterhin aus.

Enthalten sind Skripte für Quellenprüfung und Build, feste Quellprüfsummen,
der anhand einer festen Prüfsumme separat geladene Upstream-Patch, generische Konfigurationen und synthetische
CLI-/FPM-Tests. Nicht enthalten sind Kundendaten, Zugangsdaten, Serverkonfigurationen
oder fertige Binärarchive. Die Installation erfolgt im eigenen Build-Verzeichnis.

PHP 7.4 und Debian 9 liegen außerhalb ihres regulären Supports. Die alten
Bibliotheken bilden einen Kompatibilitätsstand ab; sie werden hier nicht
umfassend sicherheitsgepflegt. Es gibt kein laufendes Wartungsversprechen.

Die vollständige Anleitung steht unter [Build](BUILD.md),
[Herkunft](PROVENANCE.md), [Prüfstand und Grenzen](VALIDATION.md) und
[Betrieb/Rückbau](OPERATIONS.md). Für die öffentliche Zusammenarbeit werden
die übrigen Texte auf Englisch geführt.
