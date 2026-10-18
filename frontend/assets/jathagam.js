// Sidereal (Lahiri) birth charts and Kattam checks; verified by backend/tests/test_jathagam_engine.py.
(function (root) {
  'use strict';

  const A = root.Astronomy;
  const DEG = Math.PI / 180;
  const DAY_MS = 86400000;
  // Vimshottari year length matches backend/app/features/ai_reports/astrology.py.
  const YEAR_MS = 365.2425 * DAY_MS;
  const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'];
  const SIGN_LORDS = ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
  const OWN_SIGNS = { Sun: [4], Moon: [3], Mars: [0, 7], Mercury: [2, 5], Jupiter: [8, 11], Venus: [1, 6], Saturn: [9, 10] };
  const EXALTATION = { Sun: 0, Moon: 1, Mars: 9, Mercury: 5, Jupiter: 3, Venus: 11, Saturn: 6 };
  const DASA_LORDS = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury'];
  const DASA_YEARS = [7, 20, 6, 10, 7, 18, 16, 19, 17];
  const CHEVVAI_HOUSES = [2, 4, 7, 8, 12];
  const RAHU_KETU_HOUSES = [1, 2, 7, 8];
  const PAPA_PLANETS = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];
  const PAPA_HOUSES = [1, 2, 4, 7, 8, 12];
  const KENDRA = [1, 4, 7, 10];
  const TRIKONA = [1, 5, 9];
  const DUSTHANA = [6, 8, 12];
  const BENEFICS = ['Jupiter', 'Venus', 'Mercury'];
  const MALEFICS = ['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'];

  const norm = value => ((value % 360) + 360) % 360;
  const houseFrom = (fromSign, sign) => ((sign - fromSign + 12) % 12) + 1;

  function nutation(T) {
    const omega = (125.04452 - 1934.136261 * T) * DEG;
    const sun = (280.4665 + 36000.7698 * T) * DEG;
    const moon = (218.3165 + 481267.8813 * T) * DEG;
    return {
      longitude: (-17.20 * Math.sin(omega) - 1.32 * Math.sin(2 * sun) - 0.23 * Math.sin(2 * moon) + 0.21 * Math.sin(2 * omega)) / 3600,
      obliquity: (9.20 * Math.cos(omega) + 0.57 * Math.cos(2 * sun) + 0.10 * Math.cos(2 * moon) - 0.09 * Math.cos(2 * omega)) / 3600
    };
  }

  // Mean-equinox Lahiri ayanamsa; agrees with Swiss Ephemeris SIDM_LAHIRI to about 0.001 degree.
  const ayanamsa = T => 23.85684 + (5029.0966 * T + 1.11113 * T * T) / 3600;

  function tropicalLongitude(body, time) {
    if (body === 'Sun') return A.SunPosition(time).elon;
    if (body === 'Moon') return A.EclipticGeoMoon(time).lon;
    return A.Ecliptic(A.GeoVector(A.Body[body], time, true)).elon;
  }

  function meanNode(T) {
    return norm(125.0445479 - 1934.1362891 * T + 0.0020754 * T * T + T * T * T / 467441 - T * T * T * T / 60616000);
  }

  function ascendant(time, latitude, longitude, T) {
    const nut = nutation(T);
    const epsilon = (23.4392911 - 0.0130042 * T + nut.obliquity) * DEG;
    const theta = norm(A.SiderealTime(time) * 15 + longitude) * DEG;
    const tropical = Math.atan2(Math.cos(theta), -(Math.sin(theta) * Math.cos(epsilon) + Math.tan(latitude * DEG) * Math.sin(epsilon))) / DEG;
    return norm(tropical - ayanamsa(T) - nut.longitude);
  }

  function placement(longitude, retrograde) {
    const sign = Math.floor(longitude / 30) % 12;
    const starPosition = longitude * 27 / 360;
    const star = Math.floor(starPosition) % 27;
    return {
      longitude, sign, degree: longitude - sign * 30, star,
      pada: Math.min(4, Math.floor((starPosition - Math.floor(starPosition)) * 4) + 1),
      navamsa: Math.floor(longitude * 3 / 10) % 12,
      retrograde
    };
  }

  function dignity(planet, sign) {
    if (EXALTATION[planet] === sign) return 'exalted';
    if (EXALTATION[planet] !== undefined && (EXALTATION[planet] + 6) % 12 === sign) return 'debilitated';
    if (OWN_SIGNS[planet] && OWN_SIGNS[planet].includes(sign)) return 'own';
    return '';
  }

  function zoneOffsetMs(utcMs, timeZone) {
    const parts = {};
    new Intl.DateTimeFormat('en-US', {
      timeZone, hourCycle: 'h23', year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric'
    }).formatToParts(new Date(utcMs)).forEach(part => { parts[part.type] = part.value; });
    const wall = Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), Number(parts.hour) % 24, Number(parts.minute), Number(parts.second));
    return wall - Math.floor(utcMs / 1000) * 1000;
  }

  function localToUtc(dateText, timeText, timeZone) {
    const [year, month, day] = String(dateText).split('-').map(Number);
    const [hour, minute, second = 0] = String(timeText).split(':').map(Number);
    if (![year, month, day, hour, minute, second].every(Number.isFinite)) throw new RangeError('invalid-date-time');
    const wall = Date.UTC(year, month - 1, day, hour, minute, second);
    const candidates = new Set();
    for (const probe of [wall - DAY_MS, wall + DAY_MS]) {
      const candidate = wall - zoneOffsetMs(probe, timeZone);
      if (candidate + zoneOffsetMs(candidate, timeZone) === wall) candidates.add(candidate);
    }
    if (candidates.size !== 1) throw new RangeError(candidates.size ? 'ambiguous-time' : 'nonexistent-time');
    return [...candidates][0];
  }

  function chartAt(utcMs, latitude, longitude) {
    const time = A.MakeTime(new Date(utcMs));
    const T = time.tt / 36525;
    const nut = nutation(T);
    const shift = ayanamsa(T) + nut.longitude;
    const planets = {};
    for (const body of PLANETS) {
      const longitudeNow = norm(tropicalLongitude(body, time) - shift);
      const motion = ((tropicalLongitude(body, time.AddDays(0.5)) - tropicalLongitude(body, time.AddDays(-0.5)) + 540) % 360) - 180;
      planets[body] = placement(longitudeNow, body !== 'Sun' && body !== 'Moon' && motion < 0);
    }
    const rahu = norm(meanNode(T) - ayanamsa(T));
    planets.Rahu = placement(rahu, true);
    planets.Ketu = placement(norm(rahu + 180), true);
    return { utcMs, ayanamsa: shift, lagna: placement(ascendant(time, latitude, longitude, T), false), planets };
  }

  function chart(birth) {
    const utcMs = localToUtc(birth.birth_date, birth.birth_time, birth.timezone);
    return chartAt(utcMs, Number(birth.latitude), Number(birth.longitude));
  }

  function vimshottari(moonLongitude, birthMs) {
    const position = moonLongitude * 27 / 360;
    const first = Math.floor(position) % 9;
    let start = birthMs - (position - Math.floor(position)) * DASA_YEARS[first] * YEAR_MS;
    const periods = [];
    for (let step = 0; step < 10; step += 1) {
      const index = (first + step) % 9;
      const end = start + DASA_YEARS[index] * YEAR_MS;
      periods.push({ lord: DASA_LORDS[index], index, start, end });
      start = end;
    }
    return periods;
  }

  function bhuktis(period) {
    const total = period.end - period.start;
    let start = period.start;
    return DASA_LORDS.map((_, offset) => {
      const index = (period.index + offset) % 9;
      const end = start + total * DASA_YEARS[index] / 120;
      const result = { lord: DASA_LORDS[index], start, end };
      start = end;
      return result;
    });
  }

  const signOfHouse = (lagnaSign, house) => (lagnaSign + house - 1) % 12;
  const housesRuled = (lagnaSign, planet) => [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].filter(house => SIGN_LORDS[signOfHouse(lagnaSign, house)] === planet);
  const jupiterSupports = (chartData, sign) => [0, 4, 6, 8].some(offset => (chartData.planets.Jupiter.sign + offset) % 12 === sign);
  const levelOf = score => (score >= 2 ? 'strong' : score >= 0 ? 'moderate' : 'care');

  // Traditional functional-nature heuristic: trikona/lagna lords help, pure 6/8/12 lords and dusthana placement hinder.
  function dasaQuality(chartData, lord) {
    const place = chartData.planets[lord];
    const house = houseFrom(chartData.lagna.sign, place.sign);
    let score = 0;
    if (lord === 'Rahu' || lord === 'Ketu') {
      if ([3, 6, 11].includes(house)) score += 2;
      if ([8, 12].includes(house)) score -= 2;
      return { level: score >= 2 ? 'good' : score <= -2 ? 'challenging' : 'mixed', house, ruled: [] };
    }
    const ruled = housesRuled(chartData.lagna.sign, lord);
    const trikona = ruled.includes(5) || ruled.includes(9);
    if (trikona) score += 2;
    if (ruled.includes(1)) score += 1;
    if (!trikona && !ruled.includes(1) && ruled.some(h => DUSTHANA.includes(h))) score -= 2;
    const strength = dignity(lord, place.sign);
    if (strength === 'exalted' || strength === 'own') score += 1;
    if (strength === 'debilitated') score -= 1;
    if (DUSTHANA.includes(house)) score -= 1;
    else if (KENDRA.includes(house) || TRIKONA.includes(house)) score += 1;
    return { level: score >= 2 ? 'good' : score <= -2 ? 'challenging' : 'mixed', house, ruled };
  }

  function houseStrength(chartData, house, { maleficsHelp = false } = {}) {
    const sign = signOfHouse(chartData.lagna.sign, house);
    const lord = SIGN_LORDS[sign];
    const lordSign = chartData.planets[lord].sign;
    const lordHouse = houseFrom(chartData.lagna.sign, lordSign);
    const lordDignity = dignity(lord, lordSign);
    const occupants = Object.keys(chartData.planets).filter(planet => chartData.planets[planet].sign === sign);
    const benefics = occupants.filter(planet => BENEFICS.includes(planet));
    const malefics = occupants.filter(planet => MALEFICS.includes(planet));
    const jupiterAspect = jupiterSupports(chartData, sign) && !occupants.includes('Jupiter');
    let score = ({ exalted: 2, own: 1, debilitated: -2 })[lordDignity] || 0;
    if (DUSTHANA.includes(lordHouse)) score -= 1;
    else if (KENDRA.includes(lordHouse) || TRIKONA.includes(lordHouse)) score += 1;
    score += benefics.length;
    score += maleficsHelp ? malefics.filter(planet => planet === 'Sun' || planet === 'Mars').length : -malefics.length;
    if (jupiterAspect) score += 1;
    return { house, sign, lord, lordSign, lordHouse, lordDignity, occupants, benefics, malefics, jupiterAspect, score };
  }

  function nextPeriodOf(periods, lords, nowMs, horizonMs) {
    const minimumMs = 90 * DAY_MS;
    for (const maha of periods) {
      if (maha.end - nowMs < minimumMs || maha.start > nowMs + horizonMs) continue;
      if (lords.includes(maha.lord)) return { maha: maha.lord, bhukti: null, start: Math.max(maha.start, nowMs), end: maha.end };
      for (const sub of bhuktis(maha)) {
        if (sub.end - Math.max(sub.start, nowMs) < minimumMs || sub.start > nowMs + horizonMs) continue;
        if (lords.includes(sub.lord)) return { maha: maha.lord, bhukti: sub.lord, start: Math.max(sub.start, nowMs), end: sub.end };
      }
    }
    return null;
  }

  function lifeAreas(chartData, periods, nowMs) {
    const horizon = 20 * YEAR_MS;
    const career = houseStrength(chartData, 10, { maleficsHelp: true });
    career.level = levelOf(career.score);
    career.period = nextPeriodOf(periods, [career.lord], nowMs, horizon);

    const health = houseStrength(chartData, 1);
    health.level = levelOf(health.score);

    const children = houseStrength(chartData, 5);
    const jupiterSign = chartData.planets.Jupiter.sign;
    children.jupiterHouse = houseFrom(chartData.lagna.sign, jupiterSign);
    children.jupiterDignity = dignity('Jupiter', jupiterSign);
    if (children.jupiterDignity === 'exalted' || children.jupiterDignity === 'own') children.score += 1;
    if (children.jupiterDignity === 'debilitated' || DUSTHANA.includes(children.jupiterHouse)) children.score -= 1;
    children.level = levelOf(children.score);
    children.period = nextPeriodOf(periods, [children.lord, 'Jupiter'], nowMs, horizon);

    const marriage = houseStrength(chartData, 7);
    marriage.level = levelOf(marriage.score);
    return { career, health, children, marriage };
  }

  function jointTimeline(bride, groom, nowMs, years) {
    const horizon = nowMs + years * YEAR_MS;
    const boundaries = [nowMs, horizon];
    for (const period of [...bride.dasa.periods, ...groom.dasa.periods]) {
      if (period.start > nowMs && period.start < horizon) boundaries.push(period.start);
    }
    const points = [...new Set(boundaries)].sort((a, b) => a - b);
    const covering = (periods, at) => periods.find(period => period.start <= at && at < period.end);
    return points.slice(0, -1).map((start, index) => ({
      start, end: points[index + 1], bride: covering(bride.dasa.periods, start), groom: covering(groom.dasa.periods, start)
    }));
  }

  function analysePerson(birthChart, nowMs) {
    const { lagna, planets } = birthChart;
    const mars = planets.Mars;
    const marsFromLagna = houseFrom(lagna.sign, mars.sign);
    const marsFromMoon = houseFrom(planets.Moon.sign, mars.sign);
    const chevvaiRaw = CHEVVAI_HOUSES.includes(marsFromLagna) || CHEVVAI_HOUSES.includes(marsFromMoon);
    const cancellations = [];
    if (OWN_SIGNS.Mars.includes(mars.sign)) cancellations.push('ownSign');
    if (EXALTATION.Mars === mars.sign) cancellations.push('exalted');
    if (planets.Jupiter.sign === mars.sign) cancellations.push('withJupiter');

    const rahuHouse = houseFrom(lagna.sign, planets.Rahu.sign);
    const ketuHouse = houseFrom(lagna.sign, planets.Ketu.sign);

    const references = { lagna: lagna.sign, moon: planets.Moon.sign, venus: planets.Venus.sign };
    const papaHits = [];
    for (const [reference, sign] of Object.entries(references)) {
      for (const planet of PAPA_PLANETS) {
        const house = houseFrom(sign, planets[planet].sign);
        if (PAPA_HOUSES.includes(house)) papaHits.push({ reference, planet, house });
      }
    }

    const seventhSign = (lagna.sign + 6) % 12;
    const seventhLord = SIGN_LORDS[seventhSign];
    const occupants = Object.keys(planets).filter(planet => planets[planet].sign === seventhSign);

    const periods = vimshottari(planets.Moon.longitude, birthChart.utcMs)
      .map(period => ({ ...period, quality: dasaQuality(birthChart, period.lord).level }));
    const current = periods.find(period => period.start <= nowMs && nowMs < period.end) || null;
    const currentBhukti = current ? bhuktis(current).find(period => period.start <= nowMs && nowMs < period.end) : null;
    const next = periods.find(period => period.start > nowMs) || null;
    const birthDasa = periods[0];

    return {
      chevvai: { fromLagna: marsFromLagna, fromMoon: marsFromMoon, raw: chevvaiRaw, cancellations, dosha: chevvaiRaw && cancellations.length === 0 },
      rahuKetu: { rahuHouse, ketuHouse, dosha: RAHU_KETU_HOUSES.includes(rahuHouse) || RAHU_KETU_HOUSES.includes(ketuHouse) },
      papa: { total: papaHits.length, hits: papaHits },
      seventh: {
        sign: seventhSign, lord: seventhLord, lordSign: planets[seventhLord].sign,
        lordHouse: houseFrom(lagna.sign, planets[seventhLord].sign),
        lordDignity: dignity(seventhLord, planets[seventhLord].sign), occupants
      },
      dasa: {
        birthLord: birthDasa.lord, balanceMs: birthDasa.end - birthChart.utcMs,
        current, currentBhukti, next, periods
      },
      life: lifeAreas(birthChart, periods, nowMs)
    };
  }

  function analysePair(brideChart, groomChart, nowMs) {
    const bride = analysePerson(brideChart, nowMs);
    const groom = analysePerson(groomChart, nowMs);
    const gapMs = bride.dasa.next && groom.dasa.next ? Math.abs(bride.dasa.next.start - groom.dasa.next.start) : Infinity;
    const checks = [
      { key: 'chevvai', ok: bride.chevvai.dosha === groom.chevvai.dosha },
      { key: 'rahuKetu', ok: bride.rahuKetu.dosha === groom.rahuKetu.dosha },
      { key: 'papa', ok: groom.papa.total >= bride.papa.total },
      { key: 'dasaSandhi', ok: gapMs > YEAR_MS, gapMs }
    ];
    const failures = checks.filter(check => !check.ok).length;
    return {
      bride, groom, checks, failures, level: failures === 0 ? 'high' : failures === 1 ? 'medium' : 'low',
      timeline: jointTimeline(bride, groom, nowMs, 25)
    };
  }

  root.JathagamEngine = Object.freeze({
    localToUtc, chart, chartAt, analysePair, analysePerson, vimshottari, bhuktis, dignity, houseFrom, ayanamsa,
    dasaQuality, houseStrength, nextPeriodOf, jointTimeline,
    SIGN_LORDS, PLANET_ORDER: [...PLANETS, 'Rahu', 'Ketu'], YEAR_MS
  });
})(typeof globalThis !== 'undefined' ? globalThis : this);
