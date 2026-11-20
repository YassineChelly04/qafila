---
name: deslop-erp-dashboard
description: Turn an AI-generated (vibe-coded) ERP, admin panel, back-office tool or analytics dashboard into a professional, data-dense product UI. Diagnoses the generic defaults, then tells you what to ADD and how it should LOOK: screen archetypes, KPI band, charts, tables, status colors, record pages, forms, navigation, density, power-user features and states.
---

# De-slop an ERP or dashboard: what to add, and how it should look

Use this when someone shares an AI-built ERP, CRM, admin panel, internal tool, back office or analytics dashboard (URL, screenshot, Figma or code) and wants it to feel like a serious product that people use all day.

A product UI is not a landing page. Marketing sites sell in 5 seconds. ERP screens get used for 8 hours a day. The goals change: decisions and speed over first impressions, density over air, meaning over decoration, and consistency over surprise.

Each move is written as:

- **Add:** the move itself
- **Looks like:** what the user sees on screen when it's done right
- **How:** the design steps to get there
- **Avoid:** how the move goes wrong

---

## Phase 1: Diagnose (5 minutes)

Open the main screens with realistic data. Mark which AI defaults are present:

**Layout**
- The equal KPI row: 3 or 4 identical cards, each with a label, a big number, a green "+12.5%" and an arrow
- Every metric, chart and list in its own rounded, shadowed card, with cards inside cards
- Every screen is the same "sidebar + card grid" whatever the task
- Marketing-style air everywhere: huge padding, so a table shows 6 rows on a laptop

**Data**
- Numbers with no context (no target, no comparison, no period, no unit)
- Fake-looking data: round numbers, "John Doe", "Acme Inc", 140% retention, every trend going up
- Decorative charts: donuts and pies, gradient-filled area charts, rainbow series, 3D, a legend far from the lines, a different chart type in every card
- Numbers centered or left-aligned, digits that don't line up in columns

**Color and status**
- Gradients on status pills, color used for decoration instead of meaning
- Red/green as the only signal; the same status in different colors on different screens
- Pulsing "live" dots everywhere
- Neon accents and glows in dark mode

**Interaction and copy**
- Primary, secondary and text buttons that look almost the same
- Editing in a modal that hides the table you were working from
- "Welcome back, John 👋", "Something went wrong", "No data"
- A bare spinner, a blank first run, no error designs
- No search, no saved filters, no bulk actions, no keyboard support

Then run the **5-second test**: show the main dashboard for 5 seconds and hide it. Can someone say the one thing that matters most right now, and what they should do about it? If not, the screen shows data but doesn't tell anyone anything.

---

## Phase 2: Discovery (before changing anything)

Answer these in writing. If you can't ask, infer from the product and say what you assumed.

1. **Who uses each screen and how often?** (A warehouse operator 8 hours a day, a finance manager weekly, a CEO monthly.)
2. **Which kind of dashboard is it?**
   - **Strategic:** leaders checking health. Few high-level measures, simple displays, lots of context.
   - **Analytical:** analysts finding causes. History, comparisons, filters, drill-down.
   - **Operational:** people reacting to events. Near real-time data, strong alerts, specific detail, actions close by.
3. **The 3 to 5 questions the screen must answer** ("Which invoices are overdue and who owns them?"). Every widget has to answer one of them, or it goes.
4. **The primary metric and the primary action** for each screen.
5. **The shape of the data:** typical and worst-case row counts, longest names, largest numbers, empty values, how often it refreshes.
6. **The density tier:** comfortable (occasional users), regular (most screens), or compact (power users, big tables).
7. **References:** 2 or 3 real products whose screens solve a similar job well (for example Linear, Stripe Dashboard, Attio, Airtable, Vercel, Mercury, Notion databases, the SAP Fiori, Carbon or GitHub Primer design systems). Note exactly what you take from each.
8. **Real sample data:** a realistic dataset with messy names, long values, zeros, nulls and negative numbers. Never design on "John Doe".

---

## Phase 3: The add playbook

### A. Pick a layout for each screen's job

**A1. One archetype per screen**
- **Looks like:** screens that look different because they do different things:
  - **Overview:** a KPI band on top, 2 or 3 charts that answer the key questions, a short "needs attention" list.
  - **List + detail (triage):** a full-width table, and when you click a row, a side panel opens on the right while the table stays visible.
  - **Record page:** a header with the record's name, status and main action, the main content on the left, a summary and activity timeline on the right.
  - **Form / wizard:** a focused, narrower column with grouped sections, or numbered steps for long setups.
  - **Report / analysis:** filters across the top, one large chart, the breakdown table below.
  - **Live monitor:** a dark or calm screen readable from a distance, with very few elements and alerts that stand out.
- **How:** name the archetype for every screen before designing it.
- **Avoid:** using the same card grid for every page.

### B. The KPI band: one boss, everything in context

**B1. An anchor metric**
- **Looks like:** one primary number noticeably bigger (2 to 3 times the size of the others) in a wider cell on the left, with 2 to 4 secondary metrics smaller beside it. Cells are separated by thin hairlines, not floating shadowed cards.
- **How:** rank the metrics by the questions from Phase 2. The top one gets the big cell. Put metrics that answer the same question side by side.
- **Avoid:** four equal cards that make a vanity number look as important as the one that matters.

**B2. Every number has context**
- **Looks like:** each metric shows, in small muted text, what it's compared to: "vs. target 1.2M", "vs. last month", plus a tiny trend line (sparkline) inside the cell showing recent history. The period is always visible ("Last 30 days").
- **How:** give every number a label, a unit, a period, a comparison and, where possible, a small history. Show changes as "+4.2% vs Oct" rather than just a colored arrow.
- **Avoid:** a lone big number. Too many decimals ("$1,234,567.89" on an overview; "$1.23M" is enough).

**B3. Metrics that lead to action**
- **Looks like:** alongside the totals, counts that need someone to act: "12 invoices overdue", "3 orders blocked", each clickable, opening the filtered list.
- **How:** for operational screens, prefer "what needs me" over "how big is it".

**B4. Targets as bars, not gauges**
- **Looks like:** progress against a goal shown as a slim horizontal bar (a bullet graph): the actual value as a dark bar, the target as a small vertical tick, with light background bands for poor, OK and good.
- **Avoid:** speedometer gauges and donut "percent complete" rings. They take lots of space to show one number.

### C. Charts that answer a question

**C1. The right chart for the question**
- Change over time: a line chart (several series fine, up to about 4 or 5)
- Compare categories: a horizontal bar chart, sorted, starting at zero
- Part of a whole: a single stacked bar or a sorted bar list (not a pie)
- Distribution: a histogram
- Two measures: a scatter plot
- Exact values: a table, not a chart
- **Avoid:** pie and donut charts with many slices, radar, 3D, gradient-filled areas, or a different chart type in every card just for variety.

**C2. A headline instead of just a title**
- **Looks like:** above the chart, a short sentence that says what the chart shows ("Revenue is 8% over plan, driven by EU"), with the plain title in smaller muted text below it.
- **How:** write the takeaway first, then check the chart proves it.

**C3. Muted by default, one highlight**
- **Looks like:** most series in calm grays or soft tones; the one that matters (this year, the selected region, the problem) in the accent color. Labels sit directly at the end of each line instead of in a separate legend.
- **How:** use color only when it means something. Use one chart palette that's separate from the status colors. Make sure it works for colorblind users.

**C4. Quiet scaffolding**
- **Looks like:** light, sparse gridlines, small muted axis labels, rounded tick values (0, 50k, 100k), no chart borders, no heavy backgrounds. The data is the darkest thing in the chart.
- **How:** remove every line or label that doesn't help reading the values. Add short notes on the chart for key events ("price change", "outage").

**C5. Charts you can act on**
- **Looks like:** hovering shows a clean tooltip with the exact value, the date and the comparison; clicking a bar opens the filtered list behind it.

### D. Tables: the heart of an ERP

**D1. Columns in the right order**
- **Looks like:** the first column is something a human recognizes (customer name, order number, product), not an internal ID. Then columns in order of importance, with related columns next to each other (Qty, Unit price, Total).
- **How:** ask "what does the user look for first?" and put it on the left.

**D2. Alignment that lets you scan**
- **Looks like:** text left-aligned, numbers right-aligned with digits that line up exactly (same-width numerals), currency and units in the column header ("Amount (EUR)") rather than repeated in every cell, and IDs, codes and timestamps in a monospace face. Headers align the same way as their column.
- **Avoid:** centered numbers, mixed decimal places in one column.

**D3. Density that fits the work**
- **Looks like:** rows around 40px (compact), 48px (regular) or 56px (relaxed), with a density switch for power users. Even in compact mode, rows are easy to follow.
- **How:** choose the default density from Phase 2 and offer the switch. Long text gets cut off with "…" and shows in full on hover.
- **Avoid:** marketing-style padding that shows 6 rows per screen.

**D4. Keep your place**
- **Looks like:** the header row stays visible while you scroll, and the first column stays put when you scroll sideways. A subtle highlight follows the row under the mouse; light hairline separators or very soft zebra stripes guide the eye.

**D5. Finding records**
- **Looks like:** a toolbar directly above the table with search, filter buttons and a "views" menu. Active filters show as removable chips ("Status: Overdue ×") with a "Clear all" link, and a visible result count ("248 orders"). Sortable columns show a small arrow on the active one.
- **How:** let users save filter combinations as named views ("My overdue invoices"). Show clearly when the table is filtered.

**D6. Actions where the user looks**
- **Looks like:** at most one or two quick actions on each row (often appearing on hover), plus a "⋯" menu for the rest. When rows are selected with checkboxes, a bar slides in showing "12 selected" and the bulk actions (Approve, Export, Assign). Shift-click selects a range.
- **How:** open the details of a row in a side panel so the table stays visible. Avoid modals for long edits.

**D7. Totals and summaries**
- **Looks like:** a slightly emphasized totals row at the bottom (or top) of numeric columns, and group subtotals when the data is grouped.

**D8. Status inside the table**
- **Looks like:** a status column with small, consistent badges (see E2), so the eye can scan down for "Overdue" without reading every row.

### E. Color and status: a system with meaning

**E1. Neutral interface, one accent**
- **Looks like:** the app itself mostly in calm neutrals (off-white or a slightly tinted gray background, dark gray text), with one brand accent reserved for primary actions, the selected state and links. The data and statuses are the color in the room.
- **How:** set the neutral scale first (8 to 10 steps), slightly tinted toward the brand. Use one accent. Bright colors are kept for things that need attention.

**E2. Fixed status colors with words**
- **Looks like:** each status always has the same color everywhere: red for critical or blocked, amber for warning or needs attention, green for done or healthy, blue for info or in progress, gray for draft, archived or inactive. Every badge has a word ("Overdue"), often with a small dot or icon, in a soft tinted background with darker text. Solid, flat colors, never gradients.
- **How:** write the status-to-color map once and apply it across the app. Use a small set of statuses. Never rely on color alone.

**E3. Highlight only what needs attention**
- **Looks like:** a calm screen where a red marker or a bold amber row appears only when something crosses a threshold. Important things that are always important get emphasis from position and size, not color.
- **How:** decide the thresholds. Limit "live" pulsing indicators to one or two per screen, only for data that truly updates in real time, with a slow, gentle pulse.

**E4. Dark mode designed, not inverted**
- **Looks like:** dark grays (not pure black), slightly lighter surfaces for raised panels, softened accent and status colors, no glows or neon.

### F. Record pages and forms

**F1. A record header that answers "what is this?"**
- **Looks like:** at the top of the record: the human name or number, a status badge, 3 to 5 key facts in a row (customer, amount, due date, owner), the primary action as the only solid button, and secondary actions as quieter buttons or in a "⋯" menu.

**F2. Main content + side summary**
- **Looks like:** two columns: the wide left side holds the record's sections and line items; a narrower right side holds the summary, related records and an activity timeline (who changed what, when, with comments).
- **How:** group fields into named sections (Billing, Shipping, Items). Show read-only values as clean label/value pairs that turn into fields when you click Edit, or are edited inline.

**F3. Forms that are easy to fill**
- **Looks like:** labels above fields, field widths matching the expected content (a postal code field is short, an address is long), related fields side by side (City, Postal code), sections with clear headings, required fields marked, helpful hints under tricky fields, errors in red right under the field explaining how to fix it.
- **How:** one column for most forms, two only for short related pairs. Sticky footer with Save/Cancel on long forms. Show the save state ("Saved 2 min ago" or "Unsaved changes").

### G. Navigation and app shell

**G1. A sidebar organized like the business**
- **Looks like:** a sidebar grouped by area (Sales, Purchasing, Inventory, Finance, Settings) with small headings, icons plus text labels, the current page clearly highlighted, and collapsible groups. Rarely used items sit at the bottom.
- **Avoid:** 15 unlabeled icons in one long column.

**G2. Always know where you are**
- **Looks like:** a clear page title, breadcrumbs on deeper pages ("Sales / Orders / SO-10482"), and the current company, warehouse or environment visible in the top bar (especially "Test" vs "Production", which deserves a strong color).

**G3. Get anywhere fast**
- **Looks like:** a search field or a ⌘K command palette that finds records, pages and actions in one place, with recent items shown when it opens and the keyboard shortcut shown next to each action.

### H. Typography and density for data

**H1. A compact, calm type scale**
- **Looks like:** a highly readable sans serif with clear numerals; body text at 14px, dense table text at 13 to 14px, metadata never below 12px; page titles around 20 to 24px, not huge marketing headlines. Hierarchy comes from weight and gray tone more than from size.
- **How:** use only 4 or 5 sizes. Use numerals that all have the same width wherever numbers appear in columns or update live.

**H2. Tight grouping, clear separation**
- **Looks like:** related fields and controls close together, and clearly bigger gaps between groups, so the structure is visible even on a dense screen.
- **How:** use a small spacing scale (4px steps). Separate areas with hairline borders and background tints rather than shadows. Keep shadows for things that float: menus, popovers, side panels and modals.

**H3. Restrained shapes**
- **Looks like:** small corner radius (about 4 to 8px), thin 1px borders in a light tinted gray, flat surfaces. The UI looks like a precise instrument, not a toy.

### I. The power-user layer

- **Looks like:** keyboard shortcuts for the frequent actions (shown in tooltips and menus, with a "?" overlay that lists them), arrow-key navigation in tables, saved views, export to CSV/Excel, undo after destructive actions instead of only "Are you sure?", and actions that update instantly with a quiet confirmation toast.
- **How:** list the 10 most frequent actions from Phase 2 and make each one reachable in one keystroke or one click.

### J. States: the parts AI always skips

- **Loading:** grey skeleton shapes that match the real layout (rows, chart area, numbers), not a spinner in the middle of the page. Buttons show progress while keeping their label.
- **Empty (first use):** a short explanation of what will appear here, plus the action that fills it ("Import your products" / "Create your first order").
- **No results:** "No orders match these filters" with a "Clear filters" button.
- **Error:** names what failed and what to do ("Couldn't load invoices. Retry"), placed where the content would be, without breaking the rest of the screen.
- **Stale or partial data:** "Updated 3 min ago" with a refresh control; a clear note if some sources are missing.
- **No permission:** explains who can grant access instead of a blank page.
- **Extreme data:** very long names, huge numbers, zero, negative values and 10,000 rows all still look right.

### K. Copy that names real things

- **Looks like:** buttons and messages that use the actual objects of the business: "Approve 3 invoices", "Create purchase order", "No stock movements this week". Page titles describe the data ("Overdue invoices"), not "Dashboard" everywhere.
- **Avoid:** "Welcome back 👋", "Something went wrong", "Submit", "No data".

---

## Phase 4: Apply in this order

0. **Strip:** remove the decorative gradients, glows, shadows on every card, cards inside cards, pies and donuts, the pulsing dots and the fake data. Load the realistic sample data.
1. **Structure:** assign an archetype to each screen (A), and rebuild the navigation (G).
2. **Foundations:** neutral palette, one accent, the status color map (E), the type scale and spacing (H).
3. **Tables** (D), because most ERP time is spent there.
4. **KPI band and charts** (B, C).
5. **Record pages and forms** (F).
6. **States, copy and power-user features** (J, K, I).

Work one screen at a time. Compare each with its reference before moving on.

---

## Phase 5: Review like a product designer

- **5-second test** on each overview: the most important thing and the next action are obvious.
- **Squint test:** one clear focal point per screen; the primary button is the most visible control.
- **Grayscale and colorblind check:** statuses still readable through words and icons.
- **Stress test** with extreme data (long names, big numbers, empty values, thousands of rows).
- **Keyboard pass:** can you find a record, open it, edit it and save it without the mouse?
- **Consistency pass:** the same status, button and table pattern look identical on every screen.
- **Real-user check:** watch someone do their most frequent task. Count clicks and hesitations.

---

## What to hand back

1. The discovery answers (Phase 2), including each screen's archetype, primary metric and primary action.
2. A screen-by-screen spec in plain visual language: Screen / area | Before (what it looks like now) | After (what it should look like) | How (design steps).
3. The visual system described in words: fonts and sizes, neutral and accent colors, the status color map, spacing steps, row heights, corner radius, border and shadow rules.
4. A list of real things only the owner can provide (real sample data, status names, thresholds, targets).
5. If building it too: the updated screens with screenshots at laptop width (1280 to 1440px) and one smaller width.

## Principles

- A dashboard answers questions; a table supports work. Design for the decision and the task, not for a screenshot.
- Context makes a number useful: target, comparison, period, trend.
- Color means something or it isn't there.
- Density is a feature for daily users, as long as grouping and alignment stay clear.
- Consistency is the brand of a product UI: same patterns, same colors, same words everywhere.
- Design the unhappy paths as carefully as the happy one.

Distilled from: Stephen Few (Information Dashboard Design, the 13 common mistakes), Nielsen Norman Group on workplace data tables, Material Design, Carbon, SAP Fiori, GitLab Pajamas and GitHub Primer table guidelines, Adobe Spectrum and other design systems on badges, Vercel Web Interface Guidelines, Refactoring UI, Smashing Magazine (Adam Fard) on dashboard design, saasui.design on why SaaS UI looks AI-generated, the Laith Aljunaidy ux-skill dashboard guide, MUI on AI-generated admin dashboards, and Superhuman, Retool and Dynatrace on command palettes and keyboard shortcuts.
