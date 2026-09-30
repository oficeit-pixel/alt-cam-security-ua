// Canonical existing calculator rates. No market repricing.
window.ALTCAM_RATES = {
  video: {
    indoorCamera: { one: 1100, two: 800, threeToEight: 600, overEight: 500, heightFactor: 1.3 },
    outdoorCamera: { one: 1200, two: 900, threeToEight: 700, overEight: 600, heightFactor: 1.5 },
    recorderSetup: 800,
    mobileAppSetup: 150,
    speedDomeMin: 1200,
    cableIndoorPerMeter: 16,
    cableOutdoorPerMeter: 22,
    junctionBox: 250,
    bracket: 200
  },
  intercom: {
    analogKit: 1400,
    analogMobileKit: 1800,
    ipKit: 2200,
    ipPanelSurface: 1100,
    ipMonitor: 1100,
    mobilePlace: 300
  },
  access: {
    magneticLock: 700,
    lockConnection: 400,
    controller: 700,
    reader: 600,
    exitButtonSurface: 250,
    backupPower: 350,
    keyProgramming: 20
  },
  ajax: {
    starterKit: 900,
    motionIndoor: 250,
    motionOutdoor: 400,
    opening: 200,
    leak: 100,
    hubSetup: 500,
    sirenIndoor: 250,
    sirenOutdoor: 350,
    keypad: 250
  },
  additional: {
    routerSetup: 400,
    officeSetup: 500,
    remoteSetupMin: 500,
    remoteSetupMax: 1000,
    cableBoxPerMeter: 35,
    serverCabinetAssembly: 800,
    powerSupply: 350,
    monitorInstall: 300
  }
};
