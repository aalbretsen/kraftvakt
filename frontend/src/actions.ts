/** The action a field gets when its appliance gets a new entity. */
import type { ActionConfig, Capabilities } from "./api";
import { domainActionsFor, initialData } from "./domain-actions";
import type { HassEntity } from "./types";
import { hasDefaultAction, isActionAvailable } from "./validation";

/**
 * Return the action to use with a new entity. An action that is not set gets the suggested domain action of the entity's domain,
 * with its values for the entity, or else the default action when the domain has one. A default or domain action that is not
 * available for the entity becomes an empty custom action. Any other action is kept.
 */
export function actionForEntity(
  capabilities: Capabilities,
  field: string,
  action: ActionConfig | null,
  entityId: string | null,
  stateObj: HassEntity | undefined,
): ActionConfig | null {
  if (action === null) {
    const suggested = Object.entries(domainActionsFor(capabilities, field, entityId)).find(([, domainAction]) => domainAction.suggested);
    if (suggested) {
      const [key, domainAction] = suggested;
      return { mode: "domain", domain_action: key, data: initialData(domainAction, stateObj) };
    }
    if (hasDefaultAction(capabilities, "appliances", field, entityId)) {
      return { mode: "default" };
    }
  }
  if (entityId !== null && !isActionAvailable(capabilities, field, entityId, action)) {
    return { mode: "custom", action: [] };
  }
  return action;
}
