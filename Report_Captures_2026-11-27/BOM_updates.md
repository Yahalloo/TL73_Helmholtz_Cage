# TL73_BOM: proposed updates (27 Nov 2026)

This is a draft for the shared Google Sheet **TL73_BOM**. I have not edited the sheet itself: it is Mazda's sheet, and the Drive connector here can only read it. All prices are in CAD. Columns follow the sheet: Item | Spec / where used | Qty | Unit | Vendor | Part no. | Unit / pack price | Cur. | Units per pack | Packs | Total CAD | Link | Price as of.

## 1. Electronics-PCB sheet: change these rows (new JLCPCB cart, 27 Nov 2026)

| Row (current text) | Change | Old | New |
|---|---|---|---|
| PCB fabrication, 5 boards, 1.6 mm, HASL | Unit price and total; "Price as of" becomes 27 Nov 2026 | 63.88 | **68.49** |
| PCB assembly (economic PCBA), 2 boards, top side | Unit price and total; spec becomes "H-bridge, current sense, MCU connections, buzzer, panel headers"; part no. = new cart number (copy it from the cart) | 180.05 | **229.41** |
| JLCPCB shipping to Canada | Unit price and total | 53.75 | **53.34** |
| *(new row)* JLCPCB coupon | Qty 1, vendor JLCPCB, total **-12.80**. Treat it like shipping, so no GST is applied | none | **-12.80** |

The JLCPCB order total becomes 297.90 merchandise + 53.34 shipping - 12.80 coupon = **338.45**. The cart shows 338.45, while the three lines add up to 338.44. That 1-cent gap is rounding in the cart.

The sheet still had the 15 Nov cart (63.88 / 180.05 / 53.75). The 30 V report used a 23 Nov cart (63.95 / 216.97 / 53.63 / -12.87 = 321.68). Neither is current any more.

## 2. Electronics-PCB sheet: new rows for the enclosure

The sheet has no enclosure lines at all. The panel connectors from the 30 V report are missing too, so they are listed here with the new panel parts. One option is to put them under a sub-heading "Enclosure (panel parts)" on Electronics-PCB.

| Item | Spec / where used | Qty | Unit | Vendor | Part no. | Unit price | Total CAD | Price as of |
|---|---|---|---|---|---|---|---|---|
| Shrouded 4 mm panel banana jack, 4 red + 4 black | Enclosure walls: +34 V / GND and coil X, Y, Z outputs | 8 | each | DigiKey.ca | Cal Test CT4397-01-2 / -0 | 4.16 | 33.28 | 23 Nov 2026 |
| 2-pin solder-cup panel connector | Coil thermistor X, Y, Z (left wall) | 3 | each | DigiKey.ca | Switchcraft EN3P2MX | 15.96 | 47.88 | 23 Nov 2026 |
| 6-pin solder-cup panel connector | Magnetometer (left wall) | 1 | each | DigiKey.ca | Switchcraft EN3P6MX | 26.84 | 26.84 | 23 Nov 2026 |
| USB-C to USB-A round panel adapter | USB to the Nucleo (right wall) | 1 | each | DigiKey.ca | Adafruit 4259 | 8.84 | 8.84 | 23 Nov 2026 |
| Emergency stop switch, 16 mm, latching, 1 NC + 1 NO, gold | Control pod deck, NC contact to J204 (DigiKey stock 666, 12-week factory lead time) | 1 | each | DigiKey.ca | EAO 51-256.025 (1948-1659-ND) | 52.20 | 52.20 | 27 Nov 2026 |
| Panel LED, 3 mm snap-in, yellow, 150 mm leads | IDLE (J203), colour confirmed by Adarsh | 1 | each | DigiKey.ca | Lumex SSI-LXH312YD-150 (SSI-LXH312YD-150-ND) | 2.14 | 2.14 | 27 Nov 2026 |
| Panel LED, 3 mm snap-in, green, 150 mm leads | RUN (J207) | 1 | each | DigiKey.ca | Lumex SSI-LXH312GD-150 (67-1191-ND) | 2.12 | 2.12 | 27 Nov 2026 |
| Panel LED, 3 mm snap-in, red, 150 mm leads | FAULT (J208) | 1 | each | DigiKey.ca | Lumex SSI-LXH312ID-150 (67-1190-ND) | 2.09 | 2.09 | 27 Nov 2026 |
| Fan, 5 V, 40 x 40 x 10 mm, 136 mA | Lid, over the drivers, to J206. Lead must be at least 250 mm | 1 | each | DigiKey.ca | Sunon MF40100V1-1000U-A99 | **TBC** (7.71 seen, not confirmed) | TBC | |
| Fan guard, 40 mm | On top of the lid | 1 | each | DigiKey.ca | Qualtek 08149 | **TBC** (0.88 seen, not confirmed) | TBC | |
| JST XH housing, 2-pin | Plugs for the 3 LEDs, stop switch and fan (J203, J207, J208, J204, J206) | 5 | each | DigiKey.ca | JST XHP-2 | **TBC** (0.16 seen, quantity break not confirmed) | TBC | |
| JST XH housing, 4-pin | Spare I/O plug (J205) | 1 | each | DigiKey.ca | JST XHP-4 | **TBC** | TBC | |
| JST XH crimp contacts | 2 per 2-pin plug + 4 for J205 | 14 | each | DigiKey.ca | JST SXH-001T-P0.6 | **TBC** | TBC | |
| M3 heat-set inserts + M3 screws | Lid screws (4 + 4) | 1 | set | estimate | - | 3.00 | 3.00 | 23 Nov 2026 |
| PETG filament for the enclosure | Base, control pod and lid. Final Fusion build: 496.1 + 110.4 cm³ = about 770 g solid (upper limit, infill uses less). Old box: 522 g | 1 | lot | any | - | 23.10 (C$30/kg) | 23.10 | 27 Nov 2026 |

The confirmed enclosure items add up to **178.39**. With the filament the total is **201.49**, plus the TBC items.

Two things to check before ordering:
- **Pre-crimped lead.** The ASPHSPH24K102 already on the sheet ("Pre-crimped wire, temp sense", 0.59) is a JST **PH**-series lead according to DigiKey, not XH. It will not crimp into the XHP-2 housings that row is meant for. Check that row and replace it with an XH-series lead or SXH-001T-P0.6 crimps.
- **Unconfirmed prices.** The fan, guard and XH housing prices come from DigiKey search pages, not product pages. Confirm them, the part numbers and the minimum order quantities before ordering.

## 3. Mating connectors (cable side)

These are in the 30 V report but not in the BOM.

| Item | Qty | Unit | Total CAD | Note |
|---|---|---|---|---|
| Switchcraft EN3C2FX 2-pin cable plug (thermistor cables) | 3 | 23.46 | 70.38 | DigiKey.ca, 23 Nov |
| Switchcraft EN3C6FX 6-pin cable plug (magnetometer cable) | 1 | 38.89 | 38.89 | DigiKey.ca, 23 Nov; showed no stock |
| Banana plug sets, Amazon (about C$35 each) | 2 | 35.00 | 70.00 | Approximate. The Connectors-Wiring sheet already has Cal Test CT2631 plugs; one of the two is probably redundant |

## 4. Effect on the totals

| | Old | New |
|---|---|---|
| Electronics-PCB subtotal | 410.58 | 451.34 (JLCPCB changes) + 178.39 enclosure = 629.73, + 23.10 filament (Printed-Consumables) + TBC |
| Mating connectors (if added) | none | 179.27 |

That adds 242.25 to the BOM (confirmed parts plus the filament), plus 179.27 more if the mating connectors are added. GST at 5 % applies to everything except the shipping and coupon lines.

Separately, the first-build cost in the report (PCB order + enclosure + mating connectors) is now **C$719.21 + TBC**. That is already above the C$690 course budget.
