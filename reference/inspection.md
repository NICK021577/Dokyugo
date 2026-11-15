# Inspected design reference

Source: https://www.figma.com/design/GAv0SnCtLW1LPy4aiuL3l9/DokyuGo-%E2%80%93-Public-Pages?node-id=0-1

The connector initially refused access. Access succeeded on the user's later link, and implementation used the actual design contexts and screenshots thereafter. The public screenshot supplied by the user shows the same eight public frames.

## Actual file contents

| Figma page | Contents |
| --- | --- |
| Public Pages (`0:1`) | Home, Documents, Document requirements, How it works, Privacy notice, Sign up, Log in, Forgot password |
| Resident pages (`19:2`) | Signed-in home, choose documents, date/time, review, confirmation, my bookings, ticket/live status, reschedule, cancel, notifications, profile |
| Design Pallete (`4:27`) | Design system (`9:177`) |

## Public screens inspected before implementation

| Frame | Node | Design size |
| --- | --- | --- |
| Home | `5:2` | 1280 × 3051 |
| Documents | `12:3` | 1280 × 2759 |
| Document requirements | `12:364` | 1280 × 1402 |
| How it works | `12:624` | 1280 × 1890 |
| Privacy notice | `12:870` | 1280 × 1548 |
| Sign up | `12:1083` | 1280 × 1040 |
| Log in | `12:1159` | 1280 × 780 |
| Forgot password | `12:1212` | 1280 × 740 |

No COMPONENT, COMPONENT_SET or INSTANCE nodes and no wired prototype reactions were found on Public Pages. The design system supplies default, hover, loading and disabled buttons; default/focused/error inputs; booked/walk-in/priority tags; and loading placeholders. The public screenshots include checkmarks, a selected illustrative slot and an expanded first FAQ. These were implemented as accessible controls or clearly illustrative preview content; live appointment choices come from the database.

Public Sans is used for interface text, with weight 800 headlines and 400–700 body/controls. Geist Mono is used for queue numbers. Both are bundled locally with their font licenses.

The palette is blue `#3C62B8`, blue tint `#D3E0F6`, red `#C9485A`, yellow `#F2C94C`, gold `#E2AE1B`, ink `#1B2640`, muted `#4A5578`, deep blue `#2F4E9A`, deep red `#A23A47`, and line `#D3DBF0`. Desktop content margins are 88px, with 48px navigation/footer margins; catalogue/how content is 820px wide. Panel/card radii, border weights and section spacing follow the contexts. Narrower layouts reflow for readability and keyboard/touch access.

Original SVG sources were downloaded into `static/dokyugo/assets/`, without changing their vector paths or SVG root geometry. Asset provenance and context variable mapping are in `assets.json`; the website uses local paths, never temporary Figma URLs. Exported context code is retained as read-only reference, not runtime application code. Static sample queue tickets remain examples; real tickets, available slots, catalogue requirements and staff status are database driven.

Placeholder fields for fees, requirements, processing times, office hours, barangay identity, privacy contact and retention period remain explicit until staff supply confirmed data. Browser QA checks local asset loading and rendered geometry. Functional changes from the static references include real form validation, real authentication, owner-only booking access and current appointment availability.

The resident portal uses the shared website system and provides working integration flows. Its extra pages are functional extensions; this work does not claim exact visual reproduction of the separately inventoried Resident pages or a native mobile build.
