# Gudat DA API – Ressourcen Center Deggendorf

**Quelle:** GET `/resources` (DA REST API)  
**Center:** deggendorf | **Group:** greiner  
**Stand:** 12.03.2026 (Test-Abruf)

---

## Übersicht

| ID | Name | staff_id | order | sichtbar |
|----|------|----------|-------|----------|
| 3 | Herbert Huber | 4000 | 32500 | nein |
| 4 | David Moser | 1039 | 555000 | nein |
| 5 | Valentin Salmansberger | 5009 | 30000 | nein |
| 6 | Info/Counter | – | 40000 | nein |
| 7 | Räderwechsel Team 1 | – | 50000 | nein |
| 8 | Räderwechsel Team 2 | – | 60000 | nein |
| 9 | Räderwechsel Team 3 | – | 70000 | nein |
| 10 | Räderwechsel Team 4 | – | 80000 | nein |
| 13 | Edith Egner | 4003 | 110000 | nein |
| 15 | Sandra Brendel | 1016 | 130000 | nein |
| 16 | Brunhilde Triendl | 1000 | 140000 | nein |
| 17 | Aleyna Irep | 1025 | 150000 | nein |
| 18 | Ilayda Sahbaz | 1030 | 160000 | nein |
| 19 | Wolfgang Scheingraber | 5005 | 170000 | nein |
| 20 | Andreas Dederer | 5004 | 180000 | nein |
| 21 | Tobias Reitmeier | 5007 | 190000 | nein |
| 22 | Jaroslaw Litwin | 5014 | 200000 | nein |
| 23 | Christian Raith | 5002 | 210000 | nein |
| 24 | Andreas Bretzendorfer | 5000 | 220000 | nein |
| 25 | Alexander Bretzendorfer | 5010 | 230000 | nein |
| 26 | Patrick Ebner | 5008 | 240000 | nein |
| 27 | Max Hampp | – | 250000 | nein |
| 28 | Christian Meyer | 1014 | 260000 | nein |
| 29 | Peter Högerl | – | 270000 | nein |
| 30 | Georg Kandler | 3000 | 280000 | nein |
| 31 | Dennis Blüml | 3003 | 290000 | nein |
| 32 | Bruno Wieland | 3001 | 300000 | nein |
| 33 | Matthias König | 3007 | 310000 | nein |
| 34 | Thomas Stangl | 3004 | 320000 | nein |
| 35 | Götz Klein | – | 265000 | nein |
| 36 | Fahrdienst | – | 105000 | nein |
| 37 | Christopher Gegenfurtner | – | 220000 | nein |
| 39 | Katrin Geppert | – | 265000 | nein |
| 40 | Katrina Kramhöller | – | 272500 | nein |
| 41 | Bianca Greindl | – | 285000 | nein |
| 42 | Brigitte Lackerbeck | – | 287500 | nein |
| 43 | Daniela Geiger | – | 288750 | nein |
| 44 | Rolf Sterr | – | 289375 | nein |
| 45 | TÜV (HU) | – | 330000 | nein |
| 46 | Smart Repair Delle | – | 340000 | nein |
| 47 | Smart Repair Lack | – | 350000 | nein |
| 48 | NW/GW Christian Meyer | – | 45000 | nein |
| 49 | DEKRA (HU) | – | 335000 | nein |
| 50 | Hagengruber (extern) | – | 370000 | nein |
| 51 | Zitzelsberger (extern) | – | 380000 | nein |
| 52 | AH Isar | – | 390000 | nein |
| 53 | Kupplungen vor Ort | – | 400000 | nein |
| 55 | Kupplung vor Ort | – | 420000 | nein |
| 56 | Luca Kreulinger | – | 430000 | nein |
| 57 | Lucas Hoffmann | – | 440000 | nein |
| 59 | Franz Loibl | – | 450000 | nein |
| 60 | Stefan Geier | – | 460000 | nein |
| 61 | Margit Loibl | – | 470000 | nein |
| 62 | Michaela Schrenk | – | 480000 | nein |
| 63 | Vanessa Groll | – | 490000 | nein |
| 64 | Jennifer Bielmeier | – | 500000 | nein |
| 65 | Helmo Naujock | – | 510000 | nein |
| 66 | AS Gutachter | – | 520000 | nein |
| 67 | Andrea Pfeffer | 1034 | 530000 | nein |
| 68 | Andreas Kraus | 4005 | 31250 | nein |
| 70 | Springer Mechanik | – | 540000 | nein |
| 71 | Michael Ulrich | – | 550000 | nein |
| 72 | Test SB | – | 565000 | nein |
| 73 | Hauptuntersuchung | – | 337500 | nein |
| 74 | Ramona Aufschläger | 1010 | 155000 | nein |
| 75 | Susanne Kerscher | 1037 | 585000 | nein |
| 76 | Doris Egginger | 1036 | 145000 | nein |
| 78 | Stephan Wittmann | 1038 | 595000 | nein |
| 79 | Luca Kreulinger (SB) | – | 590000 | nein |
| 80 | Raketenglaser | – | 605000 | nein |
| 81 | Petermüller (extern) | – | 615000 | nein |
| 82 | Jan Majer | – | 625000 | nein |

**72 Einträge gesamt.**

- **ID** = `resource_id` für API (z. B. POST /service_events).
- **staff_id** = Kundensystem-ID; Einträge mit staff_id sind oft konkrete Personen (für Zuordnung DRIVE/Locosoft relevant).
- **order** = Sortierung in Gudat.

*Aktualisieren:* `python3 scripts/gudat_fetch_resources.py deggendorf` aus Projekt-Root; Ausgabe ggf. hier einpflegen.
