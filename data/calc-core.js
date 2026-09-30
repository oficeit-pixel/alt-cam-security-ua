// Pure numerical boundaries shared by browser calculations and node tests.
(() => {
  function clampNumber(value, min, max, integer = false) {
    const n = Number(value);
    const finite = Number.isFinite(n) ? n : min;
    return Math.min(max, Math.max(min, integer ? Math.floor(finite) : finite));
  }
  function clampForm(form) {
    for (const field of form.querySelectorAll('input[type="number"]')) {
      const min = field.min === '' ? 0 : Number(field.min);
      const max = field.max === '' ? Number.MAX_SAFE_INTEGER : Number(field.max);
      field.value = String(clampNumber(field.value, min, max, field.step !== 'any'));
    }
  }
  function powerRuntime({load, capacityAh, batteryCount, voltage, dod, efficiency}) {
    load = clampNumber(load, 10, 30000);
    capacityAh = clampNumber(capacityAh, 7, 500, true);
    batteryCount = clampNumber(batteryCount, 1, 32, true);
    const effectiveWh = capacityAh * voltage * batteryCount * dod * efficiency;
    return {load, capacityAh, batteryCount, effectiveWh, runtimeHours: effectiveWh / load};
  }
  window.ALTCAM_CALC_CORE = Object.freeze({clampNumber, clampForm, powerRuntime});
})();
