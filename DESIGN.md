---
name: Meet2Notes
description: A private meeting workspace for reading transcripts and notes.
colors:
  dark-paper: "#101511"
  dark-sidebar: "#111d16"
  dark-panel: "#171d19"
  dark-ink: "#edf1ec"
  dark-muted: "#bbc7bd"
  dark-line: "#303b32"
  dark-accent: "#a8d7b7"
  dark-action: "#a4d2af"
  dark-action-hover: "#bee5c7"
  dark-active: "#314d39"
  dark-control: "#1c2820"
  dark-field: "#121a15"
typography:
  headline:
    fontFamily: "Newsreader, Georgia, serif"
    fontSize: "clamp(30px, 3vw, 40px)"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  title:
    fontFamily: "Newsreader, Georgia, serif"
    fontSize: "27px"
    fontWeight: 600
    lineHeight: 1.2
  body:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "15px"
  transcript:
    fontFamily: "Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "16px"
    lineHeight: 1.65
  navigation:
    fontSize: "14px"
    fontWeight: 550
rounded:
  control: "7px"
  panel: "8px"
spacing:
  small: "8px"
  medium: "16px"
  large: "24px"
components:
  button-primary:
    backgroundColor: "{colors.dark-action}"
    textColor: "#101b13"
    rounded: "{rounded.control}"
  button-primary-hover:
    backgroundColor: "{colors.dark-action-hover}"
    textColor: "#101b13"
  button-secondary:
    backgroundColor: "{colors.dark-control}"
    textColor: "#cedbd0"
    rounded: "{rounded.control}"
  panel:
    backgroundColor: "{colors.dark-panel}"
    textColor: "{colors.dark-ink}"
    rounded: "{rounded.panel}"
  field:
    backgroundColor: "{colors.dark-field}"
    textColor: "#e8f0e8"
    rounded: "{rounded.control}"
---

# Design System: Meet2Notes

## Overview

**Creative North Star: "The Dark Reading Room"**

A private meeting workspace gives transcripts a generous, quiet surface. Dark forest-tinted neutrals and restrained green actions support reading; editorial serif titles distinguish the workspace from its practical sans-serif controls and transcript.

The dark adaptation is the approved new direction. The existing light theme remains available and retains its inherited blue accents and pale surfaces; it shares the updated layout and heading treatment, but is not a light version of the dark palette.

**Key Characteristics:**
- Compact navigation and a wide reading surface.
- Timestamps, speaker cues and editable transcript text stay together.
- Flat surfaces, fine borders and visible focus states.
- Serif headings paired with a practical sans-serif interface.

## Colors

### Primary
- **Soft green action:** primary actions and active indicators; its lighter hover state is defined in the tokens.
- **Forest selection:** active navigation and supporting green surfaces.

### Neutral
- **Near-black paper, forest sidebar and raised panel:** separate the reading area, navigation and containers through tonal contrast.
- **Pale ink and muted sage:** primary and secondary text; fine green-gray lines divide content.
- The inherited light theme uses pale surfaces and blue controls; retain its existing theme values rather than substituting dark-theme colors.

**The Reading Contrast Rule.** Keep transcript text distinct from the background and preserve visible timestamps and speaker cues.

## Typography

**Display Font:** Newsreader, with Georgia and serif fallbacks.
**Body Font:** Inter, followed by system sans-serif fallbacks.

Page headings use the headline token; meeting titles use the title token. Transcript editors use 16px text and 1.65 line height. Navigation is 14px; timestamps are 12px with tabular numerals. Fine metadata includes 12px activity-log text. On coarse pointers, text fields use at least 16px.

## Layout

Desktop navigation is 246px wide, with the main area offset by the same amount. Page padding is 34px vertically and `clamp(24px, 3vw, 48px)` horizontally. Transcript rows are capped at 1020px and align timestamp, speaker, editor and save action. At 820px and below the main offset disappears, navigation moves to an expandable mobile menu, page padding tightens, tabs wrap, and the transcript editor moves below its cue.

## Elevation & Depth

Most reading surfaces and primary buttons are flat, using tonal differences and borders for separation. The floating post-meeting assistant retains a dark ambient shadow (`0 12px 35px rgba(0,0,0,.28)`).

## Shapes

Controls use gently rounded 7px corners; panels use 8px. The transcript canvas itself is transparent and borderless, with thin row separators and a 2px active-tab underline.

## Components

### Buttons

Primary actions use soft green with dark text and a lighter hover. Secondary and icon buttons use a dark green surface, subtle border and lighter text; their hover raises surface and border contrast. Visible keyboard focus uses a 2px green outline with 3px offset.

### Inputs and fields

Fields use a dark inset surface, green-gray border and 7px corners. Transcript editors rest transparent, then gain a dark green surface, border and 2px halo when focused. Search and text fields retain readable placeholders.

### Navigation and tabs

Desktop navigation rows are at least 44px high, with 19px line icons and a filled active state. The meeting tabs have 50px minimum height and an active underline; on mobile they wrap and use 38px minimum height.

### Transcript row

A compact timestamp button uses tabular numbers, a speaker cue identifies the voice, and the editable segment occupies the remaining width. Search matches and live segments get a subdued green background. The save control sits at the row edge; the mobile layout places the editor on its own line.

### Panels and status

Engine status and activity log use bordered dark panels with compact metadata. Status colors supplement explicit labels rather than replacing them.

## Do's and Don'ts

### Do:
- **Do** keep source timestamps and speaker cues adjacent to transcript text.
- **Do** maintain keyboard-visible focus and readable field text.
- **Do** preserve the inherited light theme when changing shared components.

### Don't:
- **Don't** turn the reading canvas into a stack of heavily shadowed cards.
- **Don't** replace the existing Utilities tab with invented features.
