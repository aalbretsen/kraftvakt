import {
  mdiAlertCircleOutline,
  mdiCancel,
  mdiCarClock,
  mdiCarOff,
  mdiClockFast,
  mdiClockOutline,
  mdiLightningBolt,
  mdiPauseCircleOutline,
  mdiPowerPlug,
  mdiStopCircleOutline,
  mdiTimerSand,
} from "@mdi/js";

import type { ChargerState, ChargerStatus, ChargingWindow } from "./api";
import { formatClockTime } from "./format";
import type { TranslationKey } from "./localize";

export type ChipKind = "on" | "off" | "alarm" | "outline" | "info" | "waiting";

/** How a chip looks: its colour and its icon, or a dot without one. */
export interface Chip {
  kind: ChipKind;
  icon?: string;
}

export const CHIP_EXCLUDED: Chip = { kind: "outline", icon: mdiCancel };

/**
 * The chip, its word and its sentence for each state of an EV charger, in the order the backend checks the states.
 * The icons and colours are those of the charger's state sensor.
 */
export const CHARGER_CHIPS: Record<ChargerState, [Chip, TranslationKey, TranslationKey]> = {
  stopped: [{ kind: "alarm", icon: mdiStopCircleOutline }, "status.chip_stopped", "status.regulation_stopped"],
  fault: [{ kind: "alarm", icon: mdiAlertCircleOutline }, "status.chip_fault", "status.fault"],
  first_decision: [{ kind: "off", icon: mdiTimerSand }, "status.chip_first_decision", "status.first_decision"],
  no_car: [{ kind: "off", icon: mdiCarOff }, "status.chip_no_car", "status.bypassed_no_car"],
  excluded: [CHIP_EXCLUDED, "status.chip_excluded", "status.excluded"],
  outside_window: [{ kind: "waiting", icon: mdiClockOutline }, "status.chip_window", "status.outside_window"],
  queued: [{ kind: "waiting", icon: mdiTimerSand }, "status.chip_queued", "status.waiting_charger"],
  starting: [{ kind: "info", icon: mdiCarClock }, "status.chip_starting", "status.starting_until"],
  charging: [{ kind: "on", icon: mdiLightningBolt }, "status.chip_charging", "status.charging_at"],
  activated: [{ kind: "on", icon: mdiPowerPlug }, "status.activated", "status.activated_not_charging"],
  override: [{ kind: "info", icon: mdiClockFast }, "status.chip_override", "status.window_overridden"],
  deactivated: [{ kind: "waiting", icon: mdiPauseCircleOutline }, "status.deactivated", "status.deactivated"],
};

/** A chip as it is shown for one EV charger: its word and its sentence with their parameters. */
export interface ChargerChip {
  chip: Chip;
  word: TranslationKey;
  sentence: TranslationKey;
  wordParams: Record<string, string | number>;
  sentenceParams: Record<string, string | number>;
}

/** Return «22» for «22:00», and the time as it is otherwise. */
function shortTime(time: string): string {
  return time.endsWith(":00") ? time.slice(0, -3) : time;
}

/** The chip of an EV charger. `queuedForRoom` holds when its group shares the power among the activated EV chargers. */
export function chargerChip(charger: ChargerStatus, language: string, window: ChargingWindow | null | undefined, queuedForRoom: boolean): ChargerChip {
  const [chip, word, sentence] = CHARGER_CHIPS[charger.state];
  if (charger.state === "outside_window" && window) {
    return { chip, word, sentence, wordParams: { start: shortTime(window.start), end: shortTime(window.end) }, sentenceParams: { ...window } };
  }
  if (charger.state === "starting" && charger.starting_until) {
    return { chip, word, sentence, wordParams: {}, sentenceParams: { time: formatClockTime(language, charger.starting_until) } };
  }
  if (charger.state === "queued" && queuedForRoom) {
    return { chip, word, sentence: "status.queued_for_room", wordParams: {}, sentenceParams: {} };
  }
  return { chip, word, sentence, wordParams: {}, sentenceParams: { current: charger.current_a ?? 0 } };
}
