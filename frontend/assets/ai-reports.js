(() => {
  'use strict';

  const API = '/api/v1/ai-reports';
  const CAPABILITY_KEY = 'rightconnect-ai-report-capabilities-v1';
  const words = {
    ta: {
      appTitle: 'தமிழ் ஜோதிடம் & கலைகள் AI அறிக்கைகள்', eyebrow: 'பாரம்பரியக் கலைகள்',
      compatibilityPageTitle: 'திருமணப் பொருத்தம்', compatibilityNav: 'திருமணப் பொருத்தம்',
      compatibilityDisclaimer: 'பன்னிரண்டு பாரம்பரிய விதிகள் ஒப்பிடப்படுகின்றன. இவை அறிவியல் கணிப்போ திருமண வெற்றியின் சதவீதமோ அல்ல. வர்ணம் ஒரு வரலாற்று, சாதி சார்ந்த வகைப்பாடு; இது யாருடைய மதிப்பையும் தீர்மானிக்காது.',
      backToRasi: 'ராசி முடிவுகளுக்குத் திரும்பு',
      rasiStepTitle: 'ராசி பொருத்தம்', rasiStepHelp: 'மணமகள், மணமகனின் ராசி மற்றும் நட்சத்திரத்தைத் தேர்ந்தெடுத்து 12 பொருத்தங்களைப் பார்க்கவும்.',
      kattamStepTitle: 'திருமணக் கட்டப் பொருத்தம்', kattamStepHelp: 'முழுமையான ஜாதகக் கணக்கிற்குப் பிறந்த தேதி, நேரம், இடம் தேவை.',
      kattamPrivacy: 'கணக்கீடு உங்கள் உலாவியிலேயே நடக்கிறது; பிறந்த விவரங்கள் எங்கும் அனுப்பப்படுவதில்லை, சேமிக்கப்படுவதில்லை.', kattamGenerate: 'கட்ட அறிக்கையை உருவாக்கு',
      printReport: 'PDF / அச்சிடு', editBirth: 'பிறப்பு விவரங்களை மாற்று', kattamTimeError: 'இந்த நேர மண்டலத்தில் அந்தப் பிறந்த நேரம் இல்லை அல்லது இருமுறை வருகிறது (பகல் ஒளி சேமிப்பு மாற்றம்). நேரத்தைச் சரிபார்க்கவும்.',
      brideName: 'பெண் பெயர் (விருப்பம்)', groomName: 'பையன் பெயர் (விருப்பம்)',
      brideRasi: 'பெண் ராசி', groomRasi: 'பையன் ராசி',
      brideStar: 'பெண் நட்சத்திரம்', groomStar: 'பையன் நட்சத்திரம்',
      selectRasi: '-- ராசியைத் தேர்ந்தெடுக்கவும் --', selectStar: '-- நட்சத்திரத்தைத் தேர்ந்தெடுக்கவும் --',
      checkRasiMatch: 'அறிக்கையை உருவாக்கு', twelveMatches: '12 பொருத்த முடிவுகள்',
      matched: 'பொருந்துகிறது', notMatched: 'பொருந்தவில்லை',
      quickDisclaimer: 'இது நீங்கள் தேர்ந்தெடுத்த ராசி, நட்சத்திரத்தின் அடிப்படையிலான ஆரம்பப் பாரம்பரிய ஒப்பீடு. முழு ஜாதகப் பொருத்தம் அல்ல.',
      viewKattam: 'கட்டப் பொருத்தத்தைப் பார்க்கவும்', editRasi: 'ராசி விவரங்களை மாற்று',
      downloadQuick: '12 பொருத்தங்களைப் பதிவிறக்கு', varnaNotice: 'வர்ணம் வரலாற்று சாதி-அடிப்படையிலான மரபு; நபரின் மதிப்பையோ திருமணத் தகுதியையோ அளவிடாது.',
      selectRasiFirst: '-- முதலில் ராசியைத் தேர்ந்தெடுக்கவும் --', padaSuffix: 'பாதம்',
      levelHigh: 'உத்தமம் — அதிகப் பொருத்தம்', levelMedium: 'மத்திமம் — நடுத்தரப் பொருத்தம்', levelLow: 'அதமம் — குறைந்த பொருத்தம்',
      rajjuWarning: 'ரஜ்ஜு பொருந்தவில்லை. பாரம்பரியத்தில் இது முக்கியமானதாகக் கருதப்படுவதால், முடிவு மத்திமத்திற்கு மேல் காட்டப்படாது.',
      profileHeading: 'இருவரின் ஜாதக விவரங்கள்', attribute: 'விவரம்', rowGana: 'கணம்', rowStar: 'நட்சத்திரம்', brideHeading: 'மணமகள்', groomHeading: 'மணமகன்', rowYoni: 'யோனி', rowRajju: 'ரஜ்ஜு', rowNadi: 'நாடி', rowLord: 'ராசி அதிபதி', matchesOutOf: 'பொருத்தங்கள்',
      skip: 'உள்ளடக்கத்திற்குச் செல்ல', language: 'மொழி', views: 'பகுதிகள்', services: 'சேவைகள்',
      chooseService: 'சேவையைத் தேர்ந்தெடுக்கவும்', loadingServices: 'சேவைகள் ஏற்றப்படுகின்றன…',
      catalogueUnavailable: 'அறிக்கை சேவையகத்தை அடைய முடியவில்லை. சேவையகத்தைத் தொடங்கி மீண்டும் முயற்சிக்கவும்.',
      compatibilityOnly: 'திருமணப் பொருத்தம் தனிப் பக்கத்தில் முதலில் உருவாக்கப்படுகிறது. மற்ற சேவைகள் தனித்தனியாக பின்னர் சேர்க்கப்படும்.',
      comingSoon: 'இந்தச் சேவை விரைவில் சேர்க்கப்படும்.',
      nadi: 'நாடி பொருத்தம்', varna: 'வர்ணப் பொருத்தம் (பாரம்பரிய வகைப்பாடு)',
      featureDisabled: 'திருமணப் பொருத்த அறிக்கை இன்னும் இயக்கப்படவில்லை.',
      providerMissing: 'AI வழங்குநரின் URL, மாடல் மற்றும் API key அமைக்கப்படவில்லை.',
      rateSaltMissing: 'AI_REPORT_RATE_SALT பாதுகாப்பாக அமைக்கப்படவில்லை.',
      ephemerisMissing: 'Swiss Ephemeris கணக்கீட்டுத் தொகுப்பு நிறுவப்படவில்லை.',
      login: 'Google மூலம் உள்நுழை', logout: 'வெளியேறு', guest: 'விருந்தினர்', signedIn: 'உள்நுழைந்துள்ளீர்கள்',
      optionalLogin: 'உள்நுழைவு விருப்பமானது. விருந்தினராகவும் அறிக்கை பெறலாம்.',
      tradition: 'பாரம்பரிய நம்பிக்கைகளை அடிப்படையாகக் கொண்டவை; அறிவியல் ஆதாரம் இல்லை. மருத்துவம், நிதி அல்லது முக்கிய முடிவுகளுக்கான ஆலோசனை அல்ல.',
      history: 'முந்தைய அறிக்கைகள்', family: 'குடும்ப விவரங்கள்',
      familyHelp: 'உங்கள் அனுமதியுடன் மட்டும் பிறந்த விவரங்கள் கணக்கில் சேமிக்கப்படும். அறிக்கை பெற சேமிக்க வேண்டியதில்லை.',
      unavailable: 'இப்போது கிடைக்கவில்லை', aiUnavailable: 'AI அறிக்கை சேவை இப்போது கிடைக்கவில்லை. பின்னர் மீண்டும் முயற்சிக்கவும்.',
      networkError: 'இணைப்பில் சிக்கல். இணைய இணைப்பைச் சரிபார்த்து மீண்டும் முயற்சிக்கவும்.',
      requestError: 'கோரிக்கையை நிறைவேற்ற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.',
      invalidError: 'விவரங்களைச் சரிபார்க்கவும். தேதி, நேரம், ஆயத்தொலைவுகள் மற்றும் நேர மண்டலம் சரியாக இருக்க வேண்டும்.',
      authError: 'இந்தச் செயலுக்கு மீண்டும் உள்நுழையவும்.', accessError: 'இந்த அறிக்கையை அணுக முடியவில்லை. உரிமையாளர் கணக்கில் உள்நுழையவும்.',
      onboardingError: 'குடும்ப விவரங்களையும் அறிக்கை வரலாற்றையும் சேமிக்க RightConnect கணக்குப் பதிவை முடிக்கவும். விருந்தினராகத் தொடர வெளியேறலாம்.',
      completeAccount: 'கணக்குப் பதிவை முடி',
      missingError: 'பதிவு கிடைக்கவில்லை.', rateError: 'அதிக கோரிக்கைகள் வந்துள்ளன. சிறிது நேரம் கழித்து முயற்சிக்கவும்.',
      unavailableError: 'சேவை தற்காலிகமாகக் கிடைக்கவில்லை. பின்னர் முயற்சிக்கவும்.',
      reload: 'மீண்டும் ஏற்று', back: 'சேவைகளுக்குத் திரும்பு', birth: 'பிறந்த விவரங்கள்', bride: 'மணமகள் பிறந்த விவரங்கள்', groom: 'மணமகன் பிறந்த விவரங்கள்',
      name: 'பெயர் (விருப்பம்)', brideDefaultName: 'பெயர் இல்லையெனில்: பெண்', groomDefaultName: 'பெயர் இல்லையெனில்: பையன்',
      birthDate: 'பிறந்த தேதி', birthTime: 'பிறந்த நேரம்', localTime: 'பிறந்த இடத்தின் உள்ளூர் நேரம்; நேரம் தெரியாவிட்டால் ஊகிக்க வேண்டாம்.',
      cityPreset: 'நகரத் தேர்வு', manualCity: 'வேறு இடம் / கைமுறை', place: 'பிறந்த இடம்', latitude: 'அட்சரேகை', longitude: 'தீர்க்கரேகை', timezone: 'IANA நேர மண்டலம்',
      birthCityOptional: 'பிறந்த ஊர் (விருப்பம்)',
      kattamPlaceHelp: 'ஊர்ப் பெயரைத் தட்டச்சு செய்யவும். காலியாக விட்டால் அல்லது ஊர் அடையாளம் காணப்படாவிட்டால் சென்னை அடிப்படையில் கணக்கிடப்படும்.',
      placeUnknown: '{name}: “{place}” ஊர் அடையாளம் காணப்படவில்லை; சென்னை (இந்திய நேரம்) அடிப்படையில் கணக்கிடப்பட்டது. லக்னம் சிறிது மாறலாம்.',
      placeMissing: '{name}: பிறந்த ஊர் கொடுக்கப்படவில்லை; சென்னை அடிப்படையில் கணக்கிடப்பட்டது. லக்னம் சிறிது மாறலாம்.',
      chooseTitle: 'எந்தப் பொருத்தம் பார்க்க வேண்டும்?', chooseRasiTitle: 'ராசி பொருத்தம்', chooseKattamTitle: 'கட்டப் பொருத்தம்',
      chooseRasiHelp: 'ராசி, நட்சத்திரம் மட்டும் தெரிந்தால் — 12 பொருத்தங்கள். பிறகு கட்டப் பொருத்தமும் பார்க்கலாம்.',
      chooseKattamHelp: 'பிறந்த தேதி, நேரம் தெரிந்தால் — நேரடியாக முழு ஜாதகப் பொருத்தம்: தோஷம், தசை, எதிர்காலம்.',
      backToChoice: 'பொருத்த வகைக்குத் திரும்பு',
      locationHelp: 'நகர மைய ஆயத்தொலைவுகள் மட்டுமே. பிறந்த இடத்திற்கேற்ப திருத்தவும். மற்ற இடங்களுக்கு சரியான ஆயத்தொலைவுகளை நீங்களே உள்ளிடவும்; தானியங்கி இடத்தேடல் இல்லை.',
      compatibilityPlaceHelp: 'பிறந்த ஊரைத் தேர்ந்தெடுக்கவும்; நேர மண்டலம் தானாக நிரப்பப்படும். இந்தப் பொருத்தக் கணக்கிற்கு அட்சரேகை, தீர்க்கரேகை தேவையில்லை.',
      confirmLocation: 'பிறந்த இடம், அட்சரேகை, தீர்க்கரேகை மற்றும் நேர மண்டலத்தைச் சரிபார்த்து உறுதிப்படுத்துகிறேன்.',
      timezoneHelp: 'எ.கா. Asia/Kolkata. பிறந்த தேதிக்கான உள்ளூர் நேர மண்டலத்தை உறுதிப்படுத்தவும்.',
      savedMember: 'சேமித்த குடும்ப உறுப்பினர்', manualMember: 'புதிய விவரங்களை உள்ளிடு',
      fullName: 'முழுப் பெயர் (ஆங்கில எழுத்துகளில்)', englishNameHelp: 'எண் கணிதத்திற்கு வழக்கமாகப் பயன்படுத்தும் ஆங்கிலப் பெயர் எழுத்துக்கூட்டலை உள்ளிடவும்.',
      englishNameError: 'பெயரை ஆங்கில எழுத்துகளில் உள்ளிடவும்.', invalidTimezone: 'சரியான IANA நேர மண்டலத்தை உள்ளிடவும்.',
      facing: 'வீடு எதிர்நோக்கும் திசை', main_door: 'முதன்மை வாசல் திசை', kitchen: 'சமையலறை அமைந்த திசை', bedroom: 'படுக்கையறை அமைந்த திசை',
      directionHelp: 'வீட்டின் மையத்திலிருந்து அறைகள் அமைந்த திசையைத் தேர்ந்தெடுக்கவும்.',
      N: 'வடக்கு', NE: 'வடகிழக்கு', E: 'கிழக்கு', SE: 'தென்கிழக்கு', S: 'தெற்கு', SW: 'தென்மேற்கு', W: 'மேற்கு', NW: 'வடமேற்கு',
      gender: 'பெயர் வகை', neutral: 'பாலினச் சார்பற்றது', male: 'ஆண்', female: 'பெண்', rasi: 'ராசி', period: 'காலம்', daily: 'தினசரி', weekly: 'வாராந்திர',
      reportConsent: 'பிறந்த விவரங்கள் சரியானவை என உறுதிப்படுத்தி, அறிக்கைக்காக அவற்றைத் தற்காலிகமாகச் சேமித்து AI சேவை வழங்குநருக்கு அனுப்ப அனுமதிக்கிறேன். குடும்பப் பட்டியலில் தானாகச் சேமிக்கப்படாது.',
      generate: 'அறிக்கை உருவாக்கு', generating: 'அறிக்கை தயாராகிறது…', loading: 'ஏற்றப்படுகிறது…', completed: 'தயார்', pending: 'தயாராகிறது', failed: 'உருவாக்க முடியவில்லை',
      failedHelp: 'இந்த அறிக்கை முழுமையடையவில்லை. இதே பதிவை மீண்டும் முயற்சிக்கலாம்.', pendingHelp: 'அறிக்கை இன்னும் தயாராகிறது. சிறிது நேரம் கழித்து நிலையைச் சரிபார்க்கவும்.',
      retry: 'மீண்டும் முயற்சி', refresh: 'நிலையைச் சரிபார்', open: 'திற', edit: 'விவரங்களைத் திருத்து', editUnavailable: 'அசல் விவரங்கள் இந்தப் பக்க நினைவில் இல்லை. புதிய அறிக்கைக்கான விவரங்களை உள்ளிடவும்.',
      copy: 'நகலெடு', download: '.txt பதிவிறக்கு', share: 'பகிர்', copied: 'அறிக்கை நகலெடுக்கப்பட்டது.', copyError: 'நகலெடுக்க முடியவில்லை. .txt கோப்பைப் பதிவிறக்கலாம்.',
      shareError: 'பகிர முடியவில்லை. .txt கோப்பைப் பதிவிறக்கலாம்.', reportTitle: 'அறிக்கை', reportId: 'அறிக்கை எண்',
      noHistory: 'முந்தைய அறிக்கைகள் இல்லை.', recovery: 'இந்த அமர்வின் அறிக்கைகள்', recoveryHelp: 'இந்த உலாவித் தாவலில் மட்டும் மீண்டும் திறக்கலாம். விருந்தினர் அணுகல் விசை பிறந்த விவரங்கள் இல்லாமல் தற்காலிகமாக வைக்கப்படும். தாவலை மூடினால் அணுகல் இழக்கப்படலாம்.',
      storageError: 'இந்தத் தாவலில் மீட்பு அணுகல் விசையைச் சேமிக்க முடியவில்லை. அறிக்கையைப் பதிவிறக்கவும்; பக்கத்தைப் புதுப்பித்தால் விருந்தினர் அணுகல் இழக்கப்படும்.',
      emptyFamily: 'சேமித்த குடும்ப உறுப்பினர்கள் இல்லை.', addMember: 'உறுப்பினரைச் சேர்', memberLabel: 'உறுப்பினர் அடையாளப் பெயர்',
      saveConsent: 'இந்தப் பிறந்த விவரங்களை என் கணக்கில் சேமிக்க வெளிப்படையாக அனுமதிக்கிறேன்.',
      saveMember: 'அனுமதியுடன் சேமி', updateMember: 'அனுமதியுடன் மாற்றங்களைச் சேமி', saved: 'குடும்ப விவரங்கள் சேமிக்கப்பட்டன.',
      editMember: 'திருத்து', deleteMember: 'நீக்கு', deleteConfirm: 'இந்த உறுப்பினரின் சேமித்த பிறந்த விவரங்களை நீக்கவா?', deleted: 'உறுப்பினர் நீக்கப்பட்டார்.',
      cancel: 'ரத்து', loginUnavailable: 'Google உள்நுழைவு இப்போது கிடைக்கவில்லை. விருந்தினராகத் தொடரலாம்.', loginFailed: 'உள்நுழைவு நிறைவேறவில்லை. மீண்டும் முயற்சிக்கவும்.',
      familyError: 'குடும்ப விவரங்களை ஏற்ற முடியவில்லை. மீண்டும் முயற்சிக்கவும்.', operationBusy: 'நடைபெறும் கோரிக்கை முடியும் வரை காத்திருக்கவும்.',
      dateError: '1900 முதல் இன்று வரையிலான பிறந்த தேதியை உள்ளிடவும்.', invalidResponse: 'சேவையிலிருந்து சரியான பதில் வரவில்லை. மீண்டும் முயற்சிக்கவும்.',
      requiredField: 'இந்த விவரத்தை நிரப்பவும்.', requiredConsent: 'தொடர இந்த உறுதிப்படுத்தல் தேவை.',
      invalidField: 'இந்த விவரத்தைச் சரிபார்த்து சரியாக உள்ளிடவும்.', invalidNumber: 'குறிப்பிட்ட வரம்பிற்குள் சரியான எண்ணை உள்ளிடவும்.'
    },
    en: {
      appTitle: 'Tamil Astrology & Arts AI Reports', eyebrow: 'Traditional arts', skip: 'Skip to content', language: 'Language', views: 'Views', services: 'Services',
      compatibilityPageTitle: 'Marriage Compatibility', compatibilityNav: 'Marriage compatibility',
      compatibilityDisclaimer: 'This compares twelve traditional rules. They are not scientific predictions or a marriage-success percentage. Varna is a historical caste-coded classification; it does not determine anyone’s worth.',
      backToRasi: 'Back to Rasi results',
      rasiStepTitle: 'Rasi matching', rasiStepHelp: 'Choose both Rasis and Nakshatras to see the twelve traditional checks.',
      kattamStepTitle: 'Detailed Jathaka Kattam matching', kattamStepHelp: 'A fuller chart calculation needs each person’s birth date, time and place.',
      kattamPrivacy: 'The calculation runs in your browser; birth details are not sent anywhere or stored.', kattamGenerate: 'Create Kattam report',
      printReport: 'PDF / Print', editBirth: 'Change birth details', kattamTimeError: 'This birth time does not exist or occurs twice in that timezone (daylight-saving change). Please check the time.',
      brideName: 'Bride name (optional)', groomName: 'Groom name (optional)',
      brideRasi: 'Bride Rasi', groomRasi: 'Groom Rasi',
      brideStar: 'Bride Nakshatra', groomStar: 'Groom Nakshatra',
      selectRasi: '-- Select Rasi --', selectStar: '-- Select Nakshatra --',
      checkRasiMatch: 'Create report', twelveMatches: '12 matching results',
      matched: 'Matches this rule', notMatched: 'Does not match this rule',
      quickDisclaimer: 'This is an initial traditional comparison from the selected Rasi and Nakshatra, not a full horoscope match.',
      viewKattam: 'Check detailed Kattam matching', editRasi: 'Change Rasi details',
      downloadQuick: 'Download 12 checks', varnaNotice: 'Varna is a historical caste-coded convention; it does not measure a person’s worth or marriage suitability.',
      selectRasiFirst: '-- Select a Rasi first --', padaSuffix: 'pada',
      levelHigh: 'Uthamam — high match', levelMedium: 'Mathimam — medium match', levelLow: 'Athamam — low match',
      rajjuWarning: 'Rajju does not match. Tradition treats this as important, so the verdict is capped at medium.',
      profileHeading: 'Birth-star attributes', attribute: 'Attribute', rowGana: 'Gana', rowStar: 'Nakshatra', brideHeading: 'Bride', groomHeading: 'Groom', rowYoni: 'Yoni', rowRajju: 'Rajju', rowNadi: 'Nadi', rowLord: 'Rasi lord', matchesOutOf: 'matches',
      chooseService: 'Choose a service', loadingServices: 'Loading services…', login: 'Sign in with Google', logout: 'Sign out', guest: 'Guest', signedIn: 'Signed in',
      catalogueUnavailable: 'The report API could not be reached. Start the server and try again.',
      compatibilityOnly: 'Marriage compatibility is being built first on its own page. The other services will follow as separate pages.',
      comingSoon: 'This service will be added later.', nadi: 'Nadi Porutham', varna: 'Varna Porutham (traditional classification)',
      featureDisabled: 'Marriage report generation has not been enabled.',
      providerMissing: 'Configure the AI provider URL, model and API key.',
      rateSaltMissing: 'Configure AI_REPORT_RATE_SALT as a server-side secret.',
      ephemerisMissing: 'Install the Swiss Ephemeris calculation package.',
      optionalLogin: 'Sign-in is optional. Guests can generate reports.',
      tradition: 'Based on traditional beliefs, without scientific evidence. Not advice for medical, financial or other important decisions.',
      history: 'Report history', family: 'Family details', familyHelp: 'Birth details are saved to your account only with your permission. Saving is not required for reports.',
      unavailable: 'Currently unavailable', aiUnavailable: 'AI reports are currently unavailable. Please try again later.',
      networkError: 'Connection problem. Check your internet connection and try again.', requestError: 'Could not complete the request. Please try again.',
      invalidError: 'Check your details, including date, time, coordinates and timezone.', authError: 'Please sign in again for this action.',
      accessError: 'This report cannot be accessed. Sign in with its owner account.', missingError: 'Record not found.', rateError: 'Too many requests. Please try again shortly.',
      onboardingError: 'Complete RightConnect registration to save family details and account history. You can sign out to continue as a guest.',
      completeAccount: 'Complete registration',
      unavailableError: 'The service is temporarily unavailable. Please try again later.', reload: 'Reload', back: 'Back to services',
      birth: 'Birth details', bride: 'Bride’s details (பெண்)', groom: 'Groom’s details (பையன்)', name: 'Name (optional)',
      brideDefaultName: 'If blank, the report will say பெண்', groomDefaultName: 'If blank, the report will say பையன்',
      birthDate: 'Birth date', birthTime: 'Birth time',
      localTime: 'Local time at the birthplace. Do not guess an unknown birth time.', cityPreset: 'City preset', manualCity: 'Other place / manual',
      place: 'Birthplace', latitude: 'Latitude', longitude: 'Longitude', timezone: 'IANA timezone',
      birthCityOptional: 'Birth city (optional)',
      kattamPlaceHelp: 'Type the birth city. If it is left blank or not recognised, Chennai is used for the calculation.',
      placeUnknown: '{name}: “{place}” was not recognised, so Chennai (Indian time) was used. The Lagna may shift slightly.',
      placeMissing: '{name}: no birth city was given, so Chennai was used. The Lagna may shift slightly.',
      chooseTitle: 'Which matching would you like?', chooseRasiTitle: 'Rasi matching', chooseKattamTitle: 'Kattam matching',
      chooseRasiHelp: 'If you only know the Rasi and Nakshatra — the 12 checks. You can continue to Kattam matching afterwards.',
      chooseKattamHelp: 'If you know the birth date and time — go straight to full chart matching: dosha, dasa and future.',
      backToChoice: 'Back to matching type',
      locationHelp: 'Presets are city-centre coordinates. Adjust to the actual birthplace. Enter accurate coordinates for other places; there is no automatic geocoding.',
      compatibilityPlaceHelp: 'Choose the birthplace to fill its timezone. Latitude and longitude are not needed for this compatibility calculation.',
      confirmLocation: 'I have checked and confirm the birthplace, latitude, longitude and timezone.', timezoneHelp: 'For example, Asia/Kolkata. Confirm the local timezone for the birth date.',
      savedMember: 'Saved family member', manualMember: 'Enter new details', fullName: 'Full name (English spelling)', englishNameHelp: 'Use the English spelling of the name normally used for numerology.',
      englishNameError: 'Enter the name in English letters.', invalidTimezone: 'Enter a valid IANA timezone.',
      facing: 'House facing direction', main_door: 'Main door direction', kitchen: 'Kitchen location', bedroom: 'Bedroom location', directionHelp: 'Choose room directions relative to the centre of the house.',
      N: 'North', NE: 'Northeast', E: 'East', SE: 'Southeast', S: 'South', SW: 'Southwest', W: 'West', NW: 'Northwest',
      gender: 'Name category', neutral: 'Gender neutral', male: 'Male', female: 'Female', rasi: 'Rasi', period: 'Period', daily: 'Daily', weekly: 'Weekly',
      reportConsent: 'I confirm these birth details are accurate and consent to temporary report storage and sending them to the AI provider. They will not be automatically saved to my family list.',
      generate: 'Generate report', generating: 'Preparing your report…', loading: 'Loading…', completed: 'Ready', pending: 'Preparing', failed: 'Generation failed',
      failedHelp: 'This report did not complete. You can retry the same record.', pendingHelp: 'The report is still being prepared. Check its status again shortly.',
      retry: 'Retry', refresh: 'Check status', open: 'Open', edit: 'Edit details', editUnavailable: 'Original details are not in this page’s memory. Enter details for a new report.',
      copy: 'Copy', download: 'Download .txt', share: 'Share', copied: 'Report copied.', copyError: 'Could not copy. You can download the .txt file.', shareError: 'Could not share. You can download the .txt file.',
      reportTitle: 'Report', reportId: 'Report ID', noHistory: 'No previous reports.', recovery: 'Reports in this session',
      recoveryHelp: 'Reopen reports in this browser tab. A temporary guest access key is kept without birth details. Closing the tab may lose access.',
      storageError: 'The recovery key could not be saved in this tab. Download your report; refreshing may lose guest access.',
      emptyFamily: 'No saved family members.', addMember: 'Add member', memberLabel: 'Member label', saveConsent: 'I explicitly consent to saving these birth details to my account.',
      saveMember: 'Save with consent', updateMember: 'Save changes with consent', saved: 'Family details saved.', editMember: 'Edit', deleteMember: 'Delete',
      deleteConfirm: 'Delete this member’s saved birth details?', deleted: 'Member deleted.', cancel: 'Cancel',
      loginUnavailable: 'Google sign-in is currently unavailable. You can continue as a guest.', loginFailed: 'Sign-in did not complete. Please try again.',
      familyError: 'Could not load family details. Please try again.', operationBusy: 'Please wait for the current request to finish.',
      dateError: 'Enter a birth date between 1900 and today.', invalidResponse: 'The service returned an invalid response. Please try again.',
      requiredField: 'Please fill in this detail.', requiredConsent: 'This confirmation is required to continue.',
      invalidField: 'Please check and enter a valid value.', invalidNumber: 'Enter a valid number within the specified range.'
    }
  };
  const descriptors = [
    { key: 'horoscope', page: 'jathaka-palan.html', icon: 'orbit', ta: ['ஜாதகம்', 'பிறந்த நேரம் மற்றும் இடத்தின் அடிப்படையில் பாரம்பரிய ஜாதக விளக்கம்.'], en: ['Horoscope', 'A traditional interpretation based on birth time and place.'] },
    { key: 'compatibility', page: 'thirumana-porutham.html', icon: 'heart-handshake', ta: ['திருமணப் பொருத்தம்', 'பன்னிரண்டு பாரம்பரியப் பொருத்தங்களை ஒப்பிடும் தனிப்பட்ட அறிக்கை.'], en: ['Compatibility', 'A dedicated report comparing twelve traditional checks.'] },
    { key: 'numerology', page: 'numerology.html', icon: 'binary', ta: ['எண் கணிதம்', 'ஆங்கிலப் பெயர் மற்றும் பிறந்த தேதியின் எண் கணித விளக்கம்.'], en: ['Numerology', 'Traditional number interpretations of an English name and birth date.'] },
    { key: 'vastu', page: 'vastu.html', icon: 'house', ta: ['வாஸ்து', 'வீடு மற்றும் அறைகளின் திசைகள் பற்றிய பாரம்பரியக் கருத்துகள்.'], en: ['Vastu', 'Traditional perspectives on home and room directions.'] },
    { key: 'gemstone', page: 'gemstone.html', icon: 'gem', ta: ['ரத்தினக் கற்கள்', 'பிறந்த விவரங்களின் அடிப்படையில் பாரம்பரிய ரத்தின விளக்கம்.'], en: ['Gemstones', 'Traditional gemstone interpretations using birth details.'] },
    { key: 'baby-names', page: 'baby-names.html', icon: 'baby', ta: ['குழந்தைப் பெயர்கள்', 'பிறந்த விவரங்களுடன் குழந்தைப் பெயர் பரிந்துரைகள்.'], en: ['Baby names', 'Name suggestions using birth details and a name category.'] },
    { key: 'forecast', page: 'rasi-forecast.html', icon: 'sun', ta: ['ராசி பலன்', 'தேர்ந்தெடுத்த ராசிக்கான தினசரி அல்லது வாராந்திர பாரம்பரியப் பலன்.'], en: ['Rasi forecast', 'Daily or weekly traditional readings for your selected rasi.'] }
  ];
  const cities = [
    ['Chennai', 'சென்னை', 13.0827, 80.2707, 'Asia/Kolkata', ['Madras', 'மெட்ராஸ்']],
    ['Madurai', 'மதுரை', 9.9252, 78.1198, 'Asia/Kolkata'],
    ['Coimbatore', 'கோயம்புத்தூர்', 11.0168, 76.9558, 'Asia/Kolkata', ['Kovai', 'கோவை']],
    ['Trichy', 'திருச்சி', 10.7905, 78.7047, 'Asia/Kolkata', ['Tiruchirappalli', 'Tiruchi', 'திருச்சிராப்பள்ளி']],
    ['Salem', 'சேலம்', 11.6643, 78.146, 'Asia/Kolkata'],
    ['Tirunelveli', 'திருநெல்வேலி', 8.7139, 77.7567, 'Asia/Kolkata', ['Nellai', 'நெல்லை']],
    ['Erode', 'ஈரோடு', 11.341, 77.7172, 'Asia/Kolkata'],
    ['Vellore', 'வேலூர்', 12.9165, 79.1325, 'Asia/Kolkata'],
    ['Thanjavur', 'தஞ்சாவூர்', 10.787, 79.1378, 'Asia/Kolkata', ['Tanjore', 'தஞ்சை']],
    ['Thoothukudi', 'தூத்துக்குடி', 8.7642, 78.1348, 'Asia/Kolkata', ['Tuticorin']],
    ['Nagercoil', 'நாகர்கோவில்', 8.1833, 77.4119, 'Asia/Kolkata'],
    ['Puducherry', 'புதுச்சேரி', 11.9416, 79.8083, 'Asia/Kolkata', ['Pondicherry', 'Pondy', 'பாண்டிச்சேரி']],
    ['Bengaluru', 'பெங்களூரு', 12.9716, 77.5946, 'Asia/Kolkata', ['Bangalore', 'பெங்களூர்']],
    ['Jaffna', 'யாழ்ப்பாணம்', 9.6615, 80.0255, 'Asia/Colombo'],
    ['Colombo', 'கொழும்பு', 6.9271, 79.8612, 'Asia/Colombo'],
    ['Singapore', 'சிங்கப்பூர்', 1.3521, 103.8198, 'Asia/Singapore'],
    ['Kuala Lumpur', 'கோலாலம்பூர்', 3.139, 101.6869, 'Asia/Kuala_Lumpur'],
    ['Dubai', 'துபாய்', 25.2048, 55.2708, 'Asia/Dubai'],
    ['London', 'லண்டன்', 51.5074, -0.1278, 'Europe/London']
  ];
  const rasis = {
    ta: ['மேஷம்', 'ரிஷபம்', 'மிதுனம்', 'கடகம்', 'சிம்மம்', 'கன்னி', 'துலாம்', 'விருச்சிகம்', 'தனுசு', 'மகரம்', 'கும்பம்', 'மீனம்'],
    en: ['Mesha (Aries)', 'Rishabha (Taurus)', 'Mithuna (Gemini)', 'Kataka (Cancer)', 'Simha (Leo)', 'Kanya (Virgo)', 'Tula (Libra)', 'Vrischika (Scorpio)', 'Dhanus (Sagittarius)', 'Makara (Capricorn)', 'Kumbha (Aquarius)', 'Meena (Pisces)']
  };
  const nakshatras = {
    ta: ['அசுவினி', 'பரணி', 'கார்த்திகை', 'ரோகிணி', 'மிருகசீரிடம்', 'திருவாதிரை', 'புனர்பூசம்', 'பூசம்', 'ஆயில்யம்', 'மகம்', 'பூரம்', 'உத்திரம்', 'அஸ்தம்', 'சித்திரை', 'சுவாதி', 'விசாகம்', 'அனுஷம்', 'கேட்டை', 'மூலம்', 'பூராடம்', 'உத்திராடம்', 'திருவோணம்', 'அவிட்டம்', 'சதயம்', 'பூரட்டாதி', 'உத்திரட்டாதி', 'ரேவதி'],
    en: ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashirsha', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']
  };
  const poruthamText = {
    ta: {
      names: { dina: 'தினப் பொருத்தம்', gana: 'கணப் பொருத்தம்', mahendra: 'மகேந்திரப் பொருத்தம்', stree_deergha: 'ஸ்திரீ தீர்க்கப் பொருத்தம்', yoni: 'யோனிப் பொருத்தம்', rasi: 'ராசிப் பொருத்தம்', rasi_adhipathi: 'ராசி அதிபதிப் பொருத்தம்', vasiya: 'வசியப் பொருத்தம்', rajju: 'ரஜ்ஜுப் பொருத்தம்', vedha: 'வேதைப் பொருத்தம்', nadi: 'நாடிப் பொருத்தம்', varna: 'வர்ணப் பொருத்தம்' },
      gana: { deva: 'தேவ கணம்', manushya: 'மனுஷ கணம்', rakshasa: 'ராட்சச கணம்' },
      yoni: { horse: 'குதிரை', elephant: 'யானை', sheep: 'ஆடு', snake: 'பாம்பு', dog: 'நாய்', cat: 'பூனை', rat: 'எலி', cow: 'பசு', buffalo: 'எருமை', tiger: 'புலி', deer: 'மான்', monkey: 'குரங்கு', mongoose: 'கீரி', lion: 'சிங்கம்' },
      rajju: { foot: 'பாத ரஜ்ஜு', thigh: 'தொடை (ஊரு) ரஜ்ஜு', navel: 'நாபி (உதர) ரஜ்ஜு', neck: 'கண்ட ரஜ்ஜு', head: 'சிரசு ரஜ்ஜு' },
      nadi: { adi: 'ஆதி நாடி', madhya: 'மத்திய நாடி', antya: 'அந்திய நாடி' },
      lord: { Sun: 'சூரியன்', Moon: 'சந்திரன்', Mars: 'செவ்வாய்', Mercury: 'புதன்', Jupiter: 'குரு', Venus: 'சுக்கிரன்', Saturn: 'சனி' },
      varna: { brahmin: 'பிராமண', kshatriya: 'சத்திரிய', vaishya: 'வைசிய', shudra: 'சூத்திர' },
      explain: {
        dina: (d) => `பெண் நட்சத்திரத்திலிருந்து ஆண் நட்சத்திரம் ${d.count}-வது. 9-ஆல் வகுத்த மீதி ${d.remainder}; மீதி 2, 4, 6, 8 அல்லது 0 எனில் பொருத்தம்.`,
        gana: (d, x) => `பெண்: ${x.gana[d.bride]}, ஆண்: ${x.gana[d.groom]}. ஒரே கணம் அல்லது தேவ–மனுஷ கணங்கள் எனில் பொருத்தம்; ராட்சச கணம் ராட்சச கணத்துடன் மட்டும் பொருந்தும்.`,
        mahendra: (d) => `எண்ணிக்கை ${d.count}. 4, 7, 10, 13, 16, 19, 22, 25 ஆக இருந்தால் பொருத்தம்.`,
        stree_deergha: (d) => `எண்ணிக்கை ${d.count}. 13-க்கு மேல் இருந்தால் பொருத்தம்.`,
        yoni: (d, x) => `பெண்: ${x.yoni[d.bride]}, ஆண்: ${x.yoni[d.groom]}. ${x.yoni[d.bride]}-க்குப் பகை விலங்கு ${x.yoni[d.enemy]}; பகை இல்லையெனில் பொருத்தம்.`,
        rasi: (d) => `பெண் ராசியிலிருந்து ஆண் ராசி ${d.signCount}-வது. 1, 3, 4, 7, 10 அல்லது 11 எனில் பொருத்தம்; 2/12, 5/9, 6/8 எதிர்மறை.`,
        rasi_adhipathi: (d, x) => `அதிபதிகள்: ${x.lord[d.bride]} – ${x.lord[d.groom]}. ஒரே அதிபதி அல்லது நட்பு எனில் பொருத்தம்; பகை எனில் இல்லை.`,
        vasiya: (d, x) => `பெண் ராசிக்கு வசியமான ராசி: ${x.rasiList(d.brideTargets)}. ஆண் ராசி இந்தப் பட்டியலில் இருந்தால் மட்டுமே பொருத்தம்.`,
        rajju: (d, x) => `பெண்: ${x.rajju[d.bride]}, ஆண்: ${x.rajju[d.groom]}. வெவ்வேறு ரஜ்ஜு எனில் பொருத்தம்.`,
        vedha: (d, x) => d.group.length ? `இரு நட்சத்திரங்களும் வேதை ஜோடி (${x.starList(d.group)}).` : 'இரு நட்சத்திரங்களுக்கும் இடையே வேதை இல்லை.',
        nadi: (d, x) => `பெண்: ${x.nadi[d.bride]}, ஆண்: ${x.nadi[d.groom]}. வெவ்வேறு நாடி எனில் பொருத்தம்.`,
        varna: (d, x) => `ராசி அடிப்படையிலான வர்ணம் — பெண்: ${x.varna[d.bride]}, ஆண்: ${x.varna[d.groom]}. ஆணின் வர்ணம் சமம் அல்லது மேல் எனில் பொருத்தம்.`
      }
    },
    en: {
      names: { dina: 'Dina Porutham', gana: 'Gana Porutham', mahendra: 'Mahendra Porutham', stree_deergha: 'Stree Deergha Porutham', yoni: 'Yoni Porutham', rasi: 'Rasi Porutham', rasi_adhipathi: 'Rasi Athipathi Porutham', vasiya: 'Vasiya Porutham', rajju: 'Rajju Porutham', vedha: 'Vedha Porutham', nadi: 'Nadi Porutham', varna: 'Varna Porutham' },
      gana: { deva: 'Deva gana', manushya: 'Manushya gana', rakshasa: 'Rakshasa gana' },
      yoni: { horse: 'horse', elephant: 'elephant', sheep: 'goat', snake: 'serpent', dog: 'dog', cat: 'cat', rat: 'rat', cow: 'cow', buffalo: 'buffalo', tiger: 'tiger', deer: 'deer', monkey: 'monkey', mongoose: 'mongoose', lion: 'lion' },
      rajju: { foot: 'Paada (foot) Rajju', thigh: 'Ooru (thigh) Rajju', navel: 'Naabhi (navel) Rajju', neck: 'Kanta (neck) Rajju', head: 'Siro (head) Rajju' },
      nadi: { adi: 'Adi Nadi', madhya: 'Madhya Nadi', antya: 'Antya Nadi' },
      lord: { Sun: 'Sun', Moon: 'Moon', Mars: 'Mars', Mercury: 'Mercury', Jupiter: 'Jupiter', Venus: 'Venus', Saturn: 'Saturn' },
      varna: { brahmin: 'Brahmin', kshatriya: 'Kshatriya', vaishya: 'Vaishya', shudra: 'Shudra' },
      explain: {
        dina: (d) => `The groom’s star is ${d.count} from the bride’s. Remainder after dividing by 9 is ${d.remainder}; 2, 4, 6, 8 or 0 matches.`,
        gana: (d, x) => `Bride: ${x.gana[d.bride]}, groom: ${x.gana[d.groom]}. Same gana or Deva–Manushya matches; Rakshasa matches only Rakshasa.`,
        mahendra: (d) => `Count ${d.count}. Matches at 4, 7, 10, 13, 16, 19, 22 or 25.`,
        stree_deergha: (d) => `Count ${d.count}. Matches when the count is more than 13.`,
        yoni: (d, x) => `Bride: ${x.yoni[d.bride]}, groom: ${x.yoni[d.groom]}. The ${x.yoni[d.bride]}’s enemy is the ${x.yoni[d.enemy]}; matches when they are not enemies.`,
        rasi: (d) => `The groom’s Rasi is ${d.signCount} from the bride’s. Counts 1, 3, 4, 7, 10 and 11 match; 2/12, 5/9 and 6/8 are unfavorable.`,
        rasi_adhipathi: (d, x) => `Rasi lords: ${x.lord[d.bride]} – ${x.lord[d.groom]}. Same lord or friends match; enemies do not.`,
        vasiya: (d, x) => `Vasya Rasi for the bride’s Rasi: ${x.rasiList(d.brideTargets)}. Matches only when the groom’s Rasi is in this list.`,
        rajju: (d, x) => `Bride: ${x.rajju[d.bride]}, groom: ${x.rajju[d.groom]}. Different Rajju matches.`,
        vedha: (d, x) => d.group.length ? `The two stars form a Vedha pair (${x.starList(d.group)}).` : 'The two stars do not obstruct each other.',
        nadi: (d, x) => `Bride: ${x.nadi[d.bride]}, groom: ${x.nadi[d.groom]}. Different Nadi matches.`,
        varna: (d, x) => `Rasi-based Varna — bride: ${x.varna[d.bride]}, groom: ${x.varna[d.groom]}. Matches when the groom’s is equal or higher.`
      }
    }
  };
  const state = {
    language: 'ta', services: [], aiAvailable: false, selected: null, session: null,
    client: null, members: [], membersLoaded: false, report: null, inputs: null,
    busy: false, view: 'services', familyEditor: null, capabilities: new Map(),
    compatibilityStep: 'choose', kattamFrom: null, quickMatch: null,
    authVersion: 0, reportVersion: 0, storageWarning: false, catalogueError: null
  };
  const $ = selector => document.querySelector(selector);
  const t = key => words[state.language][key] || words.ta[key] || key;
  const text = (tag, value, className) => {
    const element = document.createElement(tag);
    if (value !== undefined) element.textContent = value;
    if (className) element.className = className;
    return element;
  };
  const error = key => Object.assign(new Error(key), { key });
  const message = failure => t(failure && failure.key ? failure.key : 'requestError');
  const notice = value => {
    $('#global-status').textContent = value;
    $('#global-status').hidden = !value;
  };
  const titleFor = descriptor => {
    const service = state.services.find(item => item.key === descriptor.key);
    return service && service[`title_${state.language}`] || descriptor[state.language][0];
  };
  const descriptorFor = key => descriptors.find(item => item.key === key);
  function icons() {
    try { if (window.lucide) window.lucide.createIcons(); } catch (_) { return; }
  }
  function button(label, action, style = 'secondary', icon) {
    const control = text('button', undefined, `button ${style}`);
    control.type = 'button';
    if (icon) {
      const symbol = text('i');
      symbol.dataset.lucide = icon;
      symbol.setAttribute('aria-hidden', 'true');
      control.append(symbol);
    }
    control.append(text('span', label));
    control.addEventListener('click', action);
    return control;
  }
  function dateLabel(value) {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? '' : new Intl.DateTimeFormat(state.language === 'ta' ? 'ta-IN' : 'en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(parsed);
  }
  function validReport(value) {
    return value && typeof value.id === 'string' && ['completed', 'failed', 'pending'].includes(value.status) && typeof value.service_type === 'string';
  }
  async function request(path, { method = 'GET', body, token, authenticated = false } = {}) {
    if (authenticated && !state.session) throw error('authError');
    const headers = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (token) headers['X-Report-Token'] = token;
    if (state.session) headers.Authorization = `Bearer ${state.session.access_token}`;
    let response;
    try {
      response = await fetch(`${API}${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store', credentials: 'omit' });
    } catch (_) { throw error('networkError'); }
    if (!response.ok) {
      if (response.status === 403) {
        const problem = await response.json().catch(() => ({}));
        if (problem.detail === 'Complete account onboarding before using AI reports while signed in') throw error('onboardingError');
      }
      const key = { 400: 'invalidError', 401: 'authError', 403: 'accessError', 404: 'missingError', 409: 'operationBusy', 422: 'invalidError', 429: 'rateError', 502: 'unavailableError', 503: 'unavailableError', 504: 'unavailableError' }[response.status];
      throw error(key || 'requestError');
    }
    if (response.status === 204 || method === 'DELETE') return null;
    try { return await response.json(); } catch (_) { throw error('invalidResponse'); }
  }
  function loadCapabilities() {
    try {
      const stored = JSON.parse(sessionStorage.getItem(CAPABILITY_KEY) || '[]');
      if (Array.isArray(stored)) for (const entry of stored) {
        if (entry && typeof entry.id === 'string' && typeof entry.token === 'string' && /^[A-Za-z0-9_-]{43}$/.test(entry.token)) state.capabilities.set(entry.id, entry.token);
      }
    } catch (_) { state.storageWarning = true; }
  }
  function keepCapability(id, token) {
    if (!token) return;
    state.capabilities.set(id, token);
    try {
      sessionStorage.setItem(CAPABILITY_KEY, JSON.stringify(Array.from(state.capabilities, ([reportId, capability]) => ({ id: reportId, token: capability }))));
    } catch (_) { state.storageWarning = true; notice(t('storageError')); }
    renderRecovery();
  }
  function newToken() {
    const bytes = new Uint8Array(32);
    crypto.getRandomValues(bytes);
    return btoa(String.fromCharCode(...bytes)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function setBusy(value) {
    state.busy = value;
    document.querySelectorAll('[data-lock], [data-view], #language, #login, #logout').forEach(control => {
      control.disabled = value || (control.id === 'login' && !state.client);
    });
    document.querySelectorAll('#input-panel form, .family-editor').forEach(form => form.setAttribute('aria-busy', String(value)));
  }
  async function perform(work, statusElement, statusKey = 'loading') {
    if (state.busy) return;
    setBusy(true);
    notice('');
    let failureMessage = '';
    if (statusElement) {
      statusElement.hidden = false;
      statusElement.textContent = t(statusKey);
      statusElement.dataset.loading = 'true';
      statusElement.dataset.error = 'false';
    }
    try { await work(); } catch (failure) {
      failureMessage = message(failure);
      notice(failureMessage);
      if (statusElement) statusElement.textContent = failureMessage;
    }
    finally {
      if (statusElement) {
        statusElement.hidden = !failureMessage;
        statusElement.dataset.loading = 'false';
        statusElement.dataset.error = String(Boolean(failureMessage));
      }
      setBusy(false);
      icons();
    }
  }
  function updateLanguageText() {
    document.documentElement.lang = state.language;
    document.title = `${t(document.body.dataset.servicePage === 'compatibility' ? 'compatibilityPageTitle' : 'appTitle')} | RightConnect`;
    document.querySelectorAll('[data-i18n]').forEach(element => { element.textContent = t(element.dataset.i18n); });
    document.querySelectorAll('[data-i18n-aria]').forEach(element => { element.setAttribute('aria-label', t(element.dataset.i18nAria)); });
    $('#account-status').textContent = t(state.session ? 'signedIn' : 'guest');
  }
  async function loadServices() {
    $('#catalogue-status').hidden = false;
    $('#catalogue-status').textContent = t('loadingServices');
    $('#reload-services').hidden = true;
    state.catalogueError = null;
    try {
      const result = await request('/services');
      if (!Array.isArray(result.services) || typeof result.ai_available !== 'boolean') throw error('invalidResponse');
      state.services = result.services;
      state.aiAvailable = result.ai_available;
    } catch (failure) {
      state.catalogueError = error('catalogueUnavailable');
      state.services = [];
      state.aiAvailable = false;
    }
    renderCatalogue();
    const pageService = document.body.dataset.servicePage;
    if (pageService) {
      const descriptor = descriptors.find(item => item.key === pageService);
      if (descriptor) {
        selectService(descriptor);
        const service = state.services.find(item => item.key === pageService);
        const reasons = service && Array.isArray(service.unavailable_reasons) ? service.unavailable_reasons : [];
        const labels = { feature_disabled: 'featureDisabled', ai_provider_missing: 'providerMissing', rate_limit_secret_missing: 'rateSaltMissing', ephemeris_missing: 'ephemerisMissing' };
        notice(state.catalogueError ? t('catalogueUnavailable') : reasons.length
          ? reasons.map(reason => t(labels[reason] || 'unavailable')).join(' ')
          : !state.aiAvailable ? t('aiUnavailable') : '');
      }
    }
  }
  function renderCatalogue() {
    const grid = $('#service-grid');
    grid.replaceChildren();
    const catalogueStatus = $('#catalogue-status');
    catalogueStatus.textContent = state.catalogueError ? message(state.catalogueError) : state.aiAvailable ? '' : t('aiUnavailable');
    catalogueStatus.hidden = !catalogueStatus.textContent;
    $('#reload-services').hidden = state.aiAvailable && !state.catalogueError;
    for (const [index, descriptor] of descriptors.entries()) {
      const service = state.services.find(item => item.key === descriptor.key);
      const available = Boolean(state.aiAvailable && service && service.available === true);
      const card = text('a', undefined, 'service-card');
      card.href = `/pages/${descriptor.page}`;
      const symbol = text('span', undefined, 'service-icon');
      symbol.setAttribute('aria-hidden', 'true');
      const icon = text('i');
      icon.dataset.lucide = descriptor.icon;
      symbol.append(icon, text('span', String(index + 1).padStart(2, '0'), 'icon-fallback'));
      card.append(symbol, text('span', titleFor(descriptor), 'service-title'));
      card.append(text('span', service && service[`description_${state.language}`] || descriptor[state.language][1], 'service-description'));
      if (!available) {
        const reasons = service && Array.isArray(service.unavailable_reasons) ? service.unavailable_reasons : [];
        const labels = { feature_disabled: 'featureDisabled', ai_provider_missing: 'providerMissing', rate_limit_secret_missing: 'rateSaltMissing', ephemeris_missing: 'ephemerisMissing' };
        if (descriptor.key === 'compatibility' && reasons.length) {
          card.append(text('span', reasons.map(reason => t(labels[reason] || 'unavailable')).join(' '), 'unavailable'));
        } else {
          card.append(text('span', descriptor.key === 'compatibility' ? t('unavailable') : t('comingSoon'), 'unavailable'));
        }
      }
      grid.append(card);
    }
    $('#compatibility-only-note')?.remove();
    if (!document.body.dataset.servicePage) {
      const guidance = text('p', t('compatibilityOnly'), 'form-help');
      guidance.id = 'compatibility-only-note';
      grid.after(guidance);
    }
    icons();
  }
  function makeField(parent, { name, label, type = 'text', value = '', required = true, help, min, max, step, maxLength, options }) {
    const wrapper = text('div', undefined, 'field');
    const id = `ai-${name.replace(/[^a-z0-9-]/gi, '-')}`;
    const caption = text('label', t(label));
    caption.htmlFor = id;
    const control = document.createElement(options ? 'select' : 'input');
    control.id = id;
    control.name = name;
    control.required = required;
    if (!options) control.type = type;
    if (options) for (const [optionValue, optionLabel] of options) {
      const option = text('option', optionLabel);
      option.value = String(optionValue);
      control.append(option);
    }
    control.value = String(value);
    if (min !== undefined) control.min = String(min);
    if (max !== undefined) control.max = String(max);
    if (step !== undefined) control.step = String(step);
    if (maxLength) control.maxLength = maxLength;
    control.autocomplete = 'off';
    wrapper.append(caption, control);
    if (help) {
      const hint = text('small', t(help));
      hint.id = `${id}-help`;
      control.setAttribute('aria-describedby', hint.id);
      wrapper.append(hint);
    }
    parent.append(wrapper);
    control.addEventListener('input', () => control.setCustomValidity(''));
    return control;
  }
  function check(parent, name, label) {
    const wrapper = text('label', undefined, 'check-label');
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.name = name;
    input.required = true;
    wrapper.append(input, text('span', t(label)));
    parent.append(wrapper);
    return input;
  }
  function today() {
    const current = new Date();
    return `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, '0')}-${String(current.getDate()).padStart(2, '0')}`;
  }
  function birthGroup(parent, prefix, heading, details = {}, allowSaved = true) {
    const compatibility = state.selected && state.selected.key === 'compatibility';
    const detailedKattam = compatibility && state.compatibilityStep === 'kattam' && (prefix === 'bride' || prefix === 'groom');
    const group = document.createElement('fieldset');
    group.dataset.birth = prefix;
    group.append(text('legend', t(heading)));
    const controls = {};
    if (state.session && allowSaved) {
      const pickerWrap = text('div', undefined, 'saved-picker');
      const picker = makeField(pickerWrap, {
        name: `${prefix}-member`, label: 'savedMember', required: false,
        options: [['', t('manualMember')], ...state.members.map(member => [member.id, member.label])]
      });
      group.append(pickerWrap);
      picker.addEventListener('change', () => {
        const member = state.members.find(item => item.id === picker.value);
        for (const [key, control] of Object.entries(controls)) control.value = member && member.details[key] !== undefined ? member.details[key] : key === 'timezone' ? 'Asia/Kolkata' : '';
        if (preset) preset.value = '';
        if (confirmation) confirmation.checked = false;
      });
    }
    const grid = text('div', undefined, 'field-grid');
    const definitions = [
      ['name', 'name', 'text', { required: false, maxLength: 100 }],
      ['birth_date', 'birthDate', 'date', { min: '1900-01-01', max: today() }],
      ['birth_time', 'birthTime', 'time', { help: 'localTime', step: 1 }]
    ];
    for (const [key, label, type, extras] of definitions) controls[key] = makeField(grid, { name: `${prefix}.${key}`, label, type, value: details[key] || '', ...extras });
    if (compatibility) controls.name.placeholder = t(prefix === 'bride' ? 'brideDefaultName' : 'groomDefaultName');
    let preset = null;
    const confirmation = null;
    if (detailedKattam) {
      controls.place = makeField(grid, { name: `${prefix}.place`, label: 'birthCityOptional', value: details.place || '', maxLength: 160, required: false, help: 'kattamPlaceHelp' });
      const suggestions = document.createElement('datalist');
      suggestions.id = `ai-${prefix}-city-list`;
      for (const city of cities) {
        const option = document.createElement('option');
        option.value = state.language === 'ta' ? city[1] : city[0];
        suggestions.append(option);
      }
      controls.place.setAttribute('list', suggestions.id);
      grid.append(suggestions);
      group.append(grid);
      parent.append(group);
      return;
    }
    preset = makeField(grid, { name: `${prefix}-city`, label: 'cityPreset', required: false, options: [['', t('manualCity')], ...cities.map(city => [city[0], state.language === 'ta' ? city[1] : city[0]])] });
    controls.place = makeField(grid, { name: `${prefix}.place`, label: 'place', value: details.place || '', maxLength: 160 });
    controls.place.minLength = 2;
    if (!compatibility) {
      controls.latitude = makeField(grid, { name: `${prefix}.latitude`, label: 'latitude', type: 'number', min: -90, max: 90, step: 'any', value: details.latitude === undefined ? '' : details.latitude });
      controls.longitude = makeField(grid, { name: `${prefix}.longitude`, label: 'longitude', type: 'number', min: -180, max: 180, step: 'any', value: details.longitude === undefined ? '' : details.longitude });
    }
    controls.timezone = makeField(grid, { name: `${prefix}.timezone`, label: 'timezone', value: details.timezone || 'Asia/Kolkata', maxLength: 80, help: 'timezoneHelp' });
    group.append(grid, text('p', t(compatibility ? 'compatibilityPlaceHelp' : 'locationHelp'), 'form-help'));
    for (const key of compatibility ? ['place', 'timezone'] : ['place', 'latitude', 'longitude', 'timezone']) controls[key].addEventListener('input', () => { if (confirmation) confirmation.checked = false; preset.value = ''; });
    preset.addEventListener('change', () => {
      const city = cities.find(item => item[0] === preset.value);
      if (city) {
        controls.place.value = state.language === 'ta' ? city[1] : city[0];
        if (controls.latitude) controls.latitude.value = city[2];
        if (controls.longitude) controls.longitude.value = city[3];
        controls.timezone.value = city[4];
      } else {
        controls.place.value = '';
        if (controls.latitude) controls.latitude.value = '';
        if (controls.longitude) controls.longitude.value = '';
        controls.timezone.value = 'Asia/Kolkata';
      }
      if (confirmation) confirmation.checked = false;
    });
    parent.append(group);
  }
  const normalisePlace = value => String(value || '').toLowerCase().replace(/[\s.,()-]/g, '');
  // No geocoding: a typed place resolves only against the city list and its aliases.
  function findCity(place) {
    const key = normalisePlace(place);
    if (!key) return null;
    const names = city => [city[0], city[1], ...(city[5] || [])].map(normalisePlace);
    return cities.find(city => names(city).includes(key))
      || cities.find(city => names(city).some(name => name.length >= 4 && key.includes(name)))
      || null;
  }
  function getKattamBirth(form, prefix, fallbackName) {
    const value = key => form.elements.namedItem(`${prefix}.${key}`).value.trim();
    const typed = value('place');
    const city = findCity(typed);
    const used = city || cities[0];
    return {
      name: value('name') || fallbackName, birth_date: value('birth_date'), birth_time: value('birth_time'),
      place: typed, place_status: city ? 'ok' : typed ? 'unknown' : 'missing',
      latitude: used[2], longitude: used[3], timezone: used[4]
    };
  }
  function getBirth(form, prefix, { coordinates = true, fallbackName = '' } = {}) {
    const value = key => form.elements.namedItem(`${prefix}.${key}`).value.trim();
    const birth = { name: value('name') || fallbackName, birth_date: value('birth_date'), birth_time: value('birth_time'), place: value('place'), timezone: value('timezone') };
    if (coordinates) {
      const coordinate = key => value(key) === '' ? '' : Number(value(key));
      birth.latitude = coordinate('latitude');
      birth.longitude = coordinate('longitude');
    }
    return birth;
  }
  function validateForm(form) {
    for (const input of form.querySelectorAll('input, select')) {
      input.setCustomValidity('');
      if (input.validity.valueMissing || (input.required && input.type !== 'checkbox' && !input.value.trim())) input.setCustomValidity(t(input.type === 'checkbox' ? 'requiredConsent' : 'requiredField'));
      else if (!input.validity.valid) input.setCustomValidity(t(input.type === 'number' ? 'invalidNumber' : 'invalidField'));
    }
    for (const input of form.querySelectorAll('input[type="date"]')) {
      if (input.value && (input.value < '1900-01-01' || input.value > today())) input.setCustomValidity(t('dateError'));
    }
    for (const input of form.querySelectorAll('input[name$=".timezone"]')) {
      try { new Intl.DateTimeFormat('en', { timeZone: input.value.trim() }).format(); }
      catch (_) { input.setCustomValidity(t('invalidTimezone')); }
    }
    const fullName = form.elements.namedItem('full_name');
    if (fullName && !/^[A-Za-z]+(?: [A-Za-z]+)*$/.test(fullName.value.trim().replace(/\s+/g, ' '))) fullName.setCustomValidity(t('englishNameError'));
    return form.reportValidity();
  }
  function readInputs(form, descriptor) {
    if (descriptor.key === 'compatibility') return {
      bride: getKattamBirth(form, 'bride', 'பெண்'),
      groom: getKattamBirth(form, 'groom', 'பையன்')
    };
    if (descriptor.key === 'numerology') return { full_name: form.elements.namedItem('full_name').value.trim(), birth_date: form.elements.namedItem('birth_date').value };
    if (descriptor.key === 'vastu') return Object.fromEntries(['facing', 'main_door', 'kitchen', 'bedroom'].map(key => [key, form.elements.namedItem(key).value]));
    if (descriptor.key === 'forecast') return { rasi: Number(form.elements.namedItem('rasi').value), period: form.elements.namedItem('period').value };
    const birth = getBirth(form, 'birth');
    return descriptor.key === 'baby-names' ? { ...birth, gender: form.elements.namedItem('gender').value } : birth;
  }
  function selectService(descriptor, inputs = {}) {
    if (state.busy) return;
    state.selected = descriptor;
    state.report = null;
    state.inputs = inputs;
    if (descriptor.key === 'compatibility' && !state.quickMatch) state.compatibilityStep = 'choose';
    state.reportVersion += 1;
    notice('');
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = true;
    renderSelectedInput(inputs);
    focusHeading('#form-title');
  }
  function renderSelectedInput(inputs = {}) {
    if (state.selected && state.selected.key === 'compatibility' && state.compatibilityStep === 'choose') {
      renderCompatibilityChoice();
      return;
    }
    if (state.selected && state.selected.key === 'compatibility' && state.compatibilityStep === 'rasi') {
      renderQuickMatchForm(inputs);
      return;
    }
    renderInput(inputs);
  }

  function readQuickMatch(form) {
    const pick = name => {
      const value = form.elements.namedItem(name).value;
      return value === '' ? '' : Number(value);
    };
    const person = role => ({
      name: form.elements.namedItem(`${role}.name`).value.trim(),
      rasi: pick(`${role}.rasi`),
      nakshatra: pick(`${role}.nakshatra`)
    });
    return { bride: person('bride'), groom: person('groom') };
  }

  function fillStarOptions(select, rasi, selected) {
    select.replaceChildren();
    const placeholder = text('option', t(rasi === '' ? 'selectRasiFirst' : 'selectStar'));
    placeholder.value = '';
    select.append(placeholder);
    select.disabled = rasi === '';
    if (rasi === '') return;
    for (const { star, padas } of window.PoruthamRules.starsForRasi(Number(rasi))) {
      const suffix = padas.length < 4 ? ` (${padas.join(', ')} ${t('padaSuffix')})` : '';
      const option = text('option', `${nakshatras[state.language][star]}${suffix}`);
      option.value = String(star);
      select.append(option);
    }
    select.value = [...select.options].some(option => option.value === String(selected)) ? String(selected) : '';
  }

  function captureSelectedInputs() {
    if (!state.selected) return state.inputs;
    if (state.selected.key === 'compatibility' && state.compatibilityStep === 'choose') return state.inputs;
    if (state.selected.key === 'compatibility' && state.compatibilityStep === 'rasi') {
      if (!state.quickMatch && $('#input-panel form')) state.inputs = readQuickMatch($('#input-panel form'));
      else if (state.quickInputs) state.inputs = state.quickInputs;
      return state.inputs;
    }
    if (!$('#input-panel form')) return state.inputs;
    state.inputs = readInputs($('#input-panel form'), state.selected);
    return state.inputs;
  }

  function rerenderSelectedInput() {
    if (state.selected && state.selected.key === 'compatibility' && state.compatibilityStep === 'rasi' && state.quickMatch) {
      renderQuickMatchResults();
      return;
    }
    renderSelectedInput(state.inputs || {});
  }

  function showCompatibilityChoice() {
    $('#report-panel').hidden = true;
    state.compatibilityStep = 'choose';
    renderCompatibilityChoice();
    focusHeading('#form-title');
  }

  function backFromKattam() {
    if (state.kattamFrom === 'rasi' && state.quickMatch) {
      $('#report-panel').hidden = true;
      state.compatibilityStep = 'rasi';
      renderQuickMatchResults();
      focusHeading('#form-title');
    } else {
      showCompatibilityChoice();
    }
  }

  function renderCompatibilityChoice() {
    const panel = $('#input-panel');
    panel.replaceChildren();
    panel.hidden = false;
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = true;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', t('chooseTitle'));
    heading.id = 'form-title';
    top.append(heading, button(t('back'), showCatalogue, 'quiet', 'arrow-left'));
    panel.append(top);
    const grid = text('div', undefined, 'service-grid match-choice');
    const options = [
      ['chooseRasiTitle', 'chooseRasiHelp', 'star', () => {
        state.compatibilityStep = 'rasi';
        state.quickMatch = null;
        renderQuickMatchForm(state.quickInputs || {});
        focusHeading('#form-title');
      }],
      ['chooseKattamTitle', 'chooseKattamHelp', 'layout-grid', () => {
        state.compatibilityStep = 'kattam';
        state.kattamFrom = 'choose';
        state.inputs = state.kattam ? state.kattam.inputs : {};
        renderInput(state.inputs);
        focusHeading('#form-title');
      }]
    ];
    options.forEach(([title, help, iconName, action], index) => {
      const card = text('button', undefined, 'service-card');
      card.type = 'button';
      const symbol = text('span', undefined, 'service-icon');
      symbol.setAttribute('aria-hidden', 'true');
      const icon = text('i');
      icon.dataset.lucide = iconName;
      symbol.append(icon, text('span', String(index + 1), 'icon-fallback'));
      card.append(symbol, text('span', t(title), 'service-title'), text('span', t(help), 'service-description'));
      card.addEventListener('click', action);
      grid.append(card);
    });
    panel.append(grid);
    icons();
  }

  function renderQuickMatchForm(values = {}) {
    const panel = $('#input-panel');
    panel.replaceChildren();
    panel.hidden = false;
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = true;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', t('rasiStepTitle'));
    heading.id = 'form-title';
    top.append(heading, button(t('backToChoice'), showCompatibilityChoice, 'quiet', 'arrow-left'));
    panel.append(top, text('p', t('rasiStepHelp'), 'form-help'));

    const form = document.createElement('form');
    form.noValidate = true;
    const pairs = [
      ['bride', t('brideName'), t('brideRasi'), t('brideStar')],
      ['groom', t('groomName'), t('groomRasi'), t('groomStar')]
    ];
    for (const [role, nameLabel, rasiLabel, starLabel] of pairs) {
      const saved = values[role] || {};
      const group = document.createElement('fieldset');
      group.append(text('legend', t(`${role}Heading`)));
      const fields = text('div', undefined, 'field-grid quick-match-grid');
      makeField(fields, { name: `${role}.name`, label: nameLabel, required: false, maxLength: 100, value: saved.name || '' });
      const rasiOptions = [['', t('selectRasi')], ...rasis[state.language].map((name, index) => [index, name])];
      const rasiValue = saved.rasi === undefined ? '' : saved.rasi;
      const rasiSelect = makeField(fields, { name: `${role}.rasi`, label: rasiLabel, options: rasiOptions, value: rasiValue });
      const starSelect = makeField(fields, { name: `${role}.nakshatra`, label: starLabel, options: [] });
      fillStarOptions(starSelect, String(rasiValue), saved.nakshatra === undefined ? '' : saved.nakshatra);
      rasiSelect.addEventListener('change', () => fillStarOptions(starSelect, rasiSelect.value, ''));
      group.append(fields);
      form.append(group);
    }
    const submit = text('button', t('checkRasiMatch'), 'button');
    submit.type = 'submit';
    const actions = text('div', undefined, 'form-actions');
    actions.append(submit);
    form.append(actions);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (state.busy || !validateForm(form)) return;
      const inputs = readQuickMatch(form);
      if (!inputs.bride.name) inputs.bride.name = 'பெண்';
      if (!inputs.groom.name) inputs.groom.name = 'பையன்';
      const result = window.PoruthamRules.calculate(inputs.bride.nakshatra, inputs.groom.nakshatra, inputs.bride.rasi, inputs.groom.rasi);
      state.quickMatch = { bride: inputs.bride, groom: inputs.groom, result };
      state.quickInputs = inputs;
      renderQuickMatchResults();
      focusHeading('#form-title');
    });
    panel.append(form);
    icons();
  }

  function quickAnalysis() {
    const { bride, groom, result } = state.quickMatch;
    const vocab = poruthamText[state.language];
    const helpers = {
      ...vocab,
      rasiList: indices => indices.map(index => rasis[state.language][index]).join(', '),
      starList: indices => indices.map(index => nakshatras[state.language][index]).join(' – ')
    };
    const rules = window.PoruthamRules;
    const attributes = person => ({
      rasi: rasis[state.language][person.rasi],
      star: nakshatras[state.language][person.nakshatra],
      gana: vocab.gana[rules.GANA[person.nakshatra]],
      yoni: vocab.yoni[rules.YONI[person.nakshatra]],
      rajju: vocab.rajju[rules.RAJJU[person.nakshatra]],
      nadi: vocab.nadi[rules.nadi(person.nakshatra)],
      lord: vocab.lord[rules.SIGN_LORDS[person.rasi]]
    });
    const brideAttributes = attributes(bride);
    const groomAttributes = attributes(groom);
    const rows = [['rasi', 'rasi'], ['star', 'rowStar'], ['gana', 'rowGana'], ['yoni', 'rowYoni'], ['rajju', 'rowRajju'], ['nadi', 'rowNadi'], ['lord', 'rowLord']]
      .map(([key, label]) => [t(label), brideAttributes[key], groomAttributes[key]]);
    const levelKey = { high: 'levelHigh', medium: 'levelMedium', low: 'levelLow' }[result.level];
    return {
      bride, groom, result, rows,
      verdict: `${result.matchedCount} / ${result.total} ${t('matchesOutOf')} · ${t(levelKey)}`,
      checks: result.checks.map(check => ({
        key: check.key,
        matches: check.matches,
        name: vocab.names[check.key],
        status: t(check.matches ? 'matched' : 'notMatched'),
        explanation: vocab.explain[check.key](check.details, helpers)
      }))
    };
  }

  function renderQuickMatchResults() {
    const panel = $('#input-panel');
    panel.replaceChildren();
    panel.hidden = false;
    if (!state.quickMatch) return;
    const analysis = quickAnalysis();
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', t('twelveMatches'));
    heading.id = 'form-title';
    top.append(heading, button(t('editRasi'), () => renderQuickMatchForm(state.quickInputs), 'quiet', 'arrow-left'));
    panel.append(top);

    const verdict = text('div', undefined, `match-verdict level-${analysis.result.level}`);
    verdict.setAttribute('role', 'status');
    verdict.append(text('strong', analysis.verdict), text('span', `${analysis.bride.name} · ${analysis.groom.name}`));
    if (analysis.result.rajjuFails) verdict.append(text('p', t('rajjuWarning')));
    panel.append(verdict);

    const table = text('table', undefined, 'match-profile');
    table.append(text('caption', t('profileHeading')));
    const head = text('tr');
    for (const label of [t('attribute'), analysis.bride.name, analysis.groom.name]) {
      const cell = text('th', label);
      cell.scope = 'col';
      head.append(cell);
    }
    const thead = text('thead');
    thead.append(head);
    const tbody = text('tbody');
    for (const [label, brideValue, groomValue] of analysis.rows) {
      const row = text('tr');
      const header = text('th', label);
      header.scope = 'row';
      row.append(header, text('td', brideValue), text('td', groomValue));
      tbody.append(row);
    }
    table.append(thead, tbody);
    panel.append(table);

    const list = text('ol', undefined, 'match-results');
    for (const check of analysis.checks) {
      const item = text('li', undefined, `match-result ${check.matches ? 'is-match' : 'no-match'}`);
      item.append(text('strong', check.name), text('span', check.status, 'match-status'), text('p', check.explanation));
      if (check.key === 'varna') item.append(text('small', t('varnaNotice')));
      list.append(item);
    }
    panel.append(list, text('p', t('quickDisclaimer'), 'form-help'));

    const actions = text('div', undefined, 'form-actions match-actions');
    actions.append(button(t('viewKattam'), () => {
      state.compatibilityStep = 'kattam';
      state.kattamFrom = 'rasi';
      const inputs = { bride: { name: state.quickMatch.bride.name }, groom: { name: state.quickMatch.groom.name } };
      state.inputs = inputs;
      renderInput(inputs);
      focusHeading('#form-title');
    }, ''));
    actions.append(button(t('downloadQuick'), downloadQuickMatch, 'secondary', 'download'));
    panel.append(actions);
    icons();
  }

  function downloadQuickMatch() {
    if (!state.quickMatch) return;
    const analysis = quickAnalysis();
    const lines = [t('twelveMatches'), `${analysis.bride.name} · ${analysis.groom.name}`, analysis.verdict, ''];
    if (analysis.result.rajjuFails) lines.push(t('rajjuWarning'), '');
    lines.push(t('profileHeading'));
    for (const [label, brideValue, groomValue] of analysis.rows) lines.push(`${label}: ${brideValue} | ${groomValue}`);
    lines.push('');
    analysis.checks.forEach((check, index) => lines.push(`${index + 1}. ${check.name} — ${check.status}`, `   ${check.explanation}`));
    lines.push('', t('quickDisclaimer'), t('varnaNotice'));
    const anchor = document.createElement('a');
    anchor.href = URL.createObjectURL(new Blob(['\uFEFF', lines.join('\n')], { type: 'text/plain;charset=utf-8' }));
    anchor.download = 'rightconnect-rasi-porutham.txt';
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(anchor.href);
  }
  function focusHeading(selector) {
    const heading = $(selector);
    if (!heading) return;
    heading.tabIndex = -1;
    heading.focus({ preventScroll: true });
    heading.scrollIntoView({ block: 'start', behavior: 'auto' });
  }
  function renderInput(inputs = {}) {
    const descriptor = state.selected;
    if (!descriptor) return;
    const panel = $('#input-panel');
    panel.replaceChildren();
    panel.hidden = false;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', descriptor.key === 'compatibility' ? t('kattamStepTitle') : titleFor(descriptor));
    heading.id = 'form-title';
    top.append(heading, descriptor.key === 'compatibility'
      ? button(t(state.kattamFrom === 'rasi' && state.quickMatch ? 'backToRasi' : 'backToChoice'), backFromKattam, 'quiet', 'arrow-left')
      : button(t('back'), showCatalogue, 'quiet', 'arrow-left'));
    panel.append(top);
    const form = document.createElement('form');
    form.noValidate = true;
    const editable = document.createElement('fieldset');
    editable.dataset.lock = '';
    if (descriptor.key === 'compatibility') {
      birthGroup(editable, 'bride', 'bride', inputs.bride || {});
      birthGroup(editable, 'groom', 'groom', inputs.groom || {});
    } else if (['horoscope', 'gemstone', 'baby-names'].includes(descriptor.key)) {
      birthGroup(editable, 'birth', 'birth', inputs);
      if (descriptor.key === 'baby-names') makeField(editable, { name: 'gender', label: 'gender', value: inputs.gender || 'neutral', options: ['neutral', 'male', 'female'].map(key => [key, t(key)]) });
    } else {
      const grid = text('div', undefined, 'field-grid');
      if (descriptor.key === 'numerology') {
        makeField(grid, { name: 'full_name', label: 'fullName', value: inputs.full_name || '', maxLength: 100, help: 'englishNameHelp' });
        makeField(grid, { name: 'birth_date', label: 'birthDate', type: 'date', value: inputs.birth_date || '', min: '1900-01-01', max: today() });
      } else if (descriptor.key === 'vastu') {
        for (const key of ['facing', 'main_door', 'kitchen', 'bedroom']) makeField(grid, { name: key, label: key, value: inputs[key] || 'N', options: ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'].map(direction => [direction, t(direction)]) });
      } else if (descriptor.key === 'forecast') {
        makeField(grid, { name: 'rasi', label: 'rasi', value: inputs.rasi === undefined ? 0 : inputs.rasi, options: rasis[state.language].map((name, index) => [index, name]) });
        makeField(grid, { name: 'period', label: 'period', value: inputs.period || 'daily', options: ['daily', 'weekly'].map(key => [key, t(key)]) });
      }
      editable.append(grid);
      if (descriptor.key === 'vastu') editable.append(text('p', t('directionHelp'), 'form-help'));
    }
    if (descriptor.key === 'compatibility') editable.append(text('p', t('kattamPrivacy'), 'form-help'));
    else check(editable, 'report-consent', 'reportConsent');
    const submit = text('button', t(descriptor.key === 'compatibility' ? 'kattamGenerate' : 'generate'), 'button');
    submit.type = 'submit';
    submit.dataset.lock = '';
    const actions = text('div', undefined, 'form-actions');
    actions.append(submit);
    editable.append(actions);
    const status = text('p', '', 'inline-status');
    status.setAttribute('role', 'status');
    status.hidden = true;
    form.append(editable, status);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (state.busy || !validateForm(form)) return;
      const inputs = readInputs(form, descriptor);
      if (descriptor.key === 'compatibility') {
        state.inputs = inputs;
        try {
          const charts = { bride: window.JathagamEngine.chart(inputs.bride), groom: window.JathagamEngine.chart(inputs.groom) };
          state.kattam = { inputs, charts, nowMs: Date.now() };
        } catch (failure) {
          status.hidden = false;
          status.dataset.error = 'true';
          status.textContent = t(/time/.test(failure.message) ? 'kattamTimeError' : 'invalidError');
          return;
        }
        renderKattamReport();
        focusHeading('#report-heading');
        return;
      }
      perform(async () => {
        const token = newToken();
        const version = state.reportVersion;
        const result = await request(`/${descriptor.key}`, { method: 'POST', token, body: { inputs, language: state.language, tier: 'basic', consent: true } });
        if (!validReport(result)) throw error('invalidResponse');
        keepCapability(result.id, token);
        if (version !== state.reportVersion) return;
        state.inputs = inputs;
        acceptReport(result);
      }, status, 'generating');
    });
    panel.append(form);
    icons();
  }
  function showCatalogue() {
    if (state.busy) return;
    if (document.body.dataset.servicePage) {
      location.href = '/pages/services.html';
      return;
    }
    state.selected = null;
    state.inputs = null;
    state.report = null;
    state.quickMatch = null;
    state.quickInputs = null;
    state.compatibilityStep = 'choose';
    state.kattamFrom = null;
    state.reportVersion += 1;
    $('#input-panel').replaceChildren();
    $('#input-panel').hidden = true;
    $('#report-panel').replaceChildren();
    $('#report-panel').hidden = true;
    $('#catalogue').hidden = false;
    notice('');
    focusHeading('#catalogue-heading');
  }
  function acceptReport(result) {
    state.report = result;
    $('#input-panel').hidden = true;
    $('#catalogue').hidden = true;
    renderReport();
    focusHeading('#report-heading');
  }
  function reportText() {
    const report = state.report;
    const written = report && report.report;
    if (!written) return '';
    const sections = Array.isArray(written.sections) ? written.sections : [];
    return [written.title, ...sections.map(section => `${section.heading}\n\n${section.body}`), written.disclaimer, t('tradition')].filter(Boolean).join('\n\n');
  }
  function renderReport() {
    const panel = $('#report-panel');
    panel.replaceChildren();
    panel.hidden = false;
    const report = state.report;
    if (!report) return;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', report.report && report.report.title || t('reportTitle'));
    heading.id = 'report-heading';
    top.append(heading, button(t('back'), showCatalogue, 'quiet', 'arrow-left'));
    panel.append(top, text('p', `${t(report.status)} · ${dateLabel(report.created_at)}`, 'report-meta'));
    const operationStatus = text('p', '', 'inline-status');
    operationStatus.setAttribute('role', 'status');
    operationStatus.hidden = true;
    panel.append(operationStatus);
    if (report.status === 'completed' && report.report && Array.isArray(report.report.sections)) {
      const body = text('article', undefined, 'report-body');
      body.lang = report.language === 'en' ? 'en' : 'ta';
      for (const section of report.report.sections) {
        const block = text('section', undefined, 'report-section');
        block.append(text('h3', section.heading), text('p', section.body));
        body.append(block);
      }
      body.append(text('p', report.report.disclaimer, 'report-disclaimer'));
      panel.append(body);
    } else {
      panel.append(text('p', t(report.status === 'pending' ? 'pendingHelp' : 'failedHelp'), 'notice'));
    }
    const actions = text('div', undefined, 'report-actions');
    if (report.status === 'failed') actions.append(button(t('retry'), () => changeReport('retry', state.language, operationStatus), '', 'rotate-ccw'));
    if (report.status === 'pending') actions.append(button(t('refresh'), () => openReport(report.id), '', 'refresh-cw'));
    if (report.status === 'completed' && report.report) {
      actions.append(button(t('copy'), () => perform(async () => {
        try { await navigator.clipboard.writeText(reportText()); notice(t('copied')); }
        catch (_) { throw error('copyError'); }
      }), 'secondary', 'copy'));
      actions.append(button(t('download'), downloadReport, 'secondary', 'download'));
      if (navigator.share) actions.append(button(t('share'), () => perform(async () => {
        try { await navigator.share({ title: String(state.report.report.title || t('reportTitle')), text: reportText() }); }
        catch (failure) { if (failure.name !== 'AbortError') throw error('shareError'); }
      }), 'secondary', 'share-2'));
    }
    if (descriptorFor(report.service_type)) actions.append(button(t('edit'), () => {
      const existing = state.inputs;
      selectService(descriptorFor(report.service_type), existing || {});
      if (!existing) notice(t('editUnavailable'));
    }, 'quiet', 'pencil'));
    for (const control of actions.querySelectorAll('button')) control.dataset.lock = '';
    panel.append(actions);
    if (state.storageWarning) panel.append(text('p', t('storageError'), 'notice'));
    icons();
  }
  function downloadReport() {
    const content = reportText();
    if (!content) return;
    const link = document.createElement('a');
    const url = URL.createObjectURL(new Blob(['\uFEFF', content], { type: 'text/plain;charset=utf-8' }));
    link.href = url;
    link.download = `rightconnect-report-${String(state.report.id).replace(/[^a-zA-Z0-9_-]/g, '')}.txt`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function renderKattamReport() {
    const kattam = state.kattam;
    if (!kattam) return;
    const chennai = state.language === 'ta' ? cities[0][1] : cities[0][0];
    const shown = person => ({ ...person, place: person.place || chennai });
    const report = window.KattamReport.build({
      charts: kattam.charts, people: { bride: shown(kattam.inputs.bride), groom: shown(kattam.inputs.groom) },
      selected: state.kattamFrom === 'rasi' ? state.quickInputs : null, language: state.language,
      rasis: rasis[state.language], nakshatras: nakshatras[state.language], nowMs: kattam.nowMs
    });
    const placeNotes = [kattam.inputs.groom, kattam.inputs.bride]
      .filter(person => person.place_status && person.place_status !== 'ok')
      .map(person => t(person.place_status === 'unknown' ? 'placeUnknown' : 'placeMissing').replace('{name}', person.name).replace('{place}', person.place));
    kattam.text = placeNotes.length ? [...placeNotes, '', report.text].join('\n') : report.text;
    $('#input-panel').hidden = true;
    $('#catalogue').hidden = true;
    const panel = $('#report-panel');
    panel.replaceChildren();
    panel.hidden = false;
    const top = text('div', undefined, 'panel-top');
    const heading = text('h2', report.title);
    heading.id = 'report-heading';
    top.append(heading, button(t(state.kattamFrom === 'rasi' && state.quickMatch ? 'backToRasi' : 'backToChoice'), backFromKattam, 'quiet', 'arrow-left'));
    const actions = text('div', undefined, 'report-actions');
    actions.append(
      button(t('download'), () => {
        const link = document.createElement('a');
        const url = URL.createObjectURL(new Blob(['\uFEFF', kattam.text], { type: 'text/plain;charset=utf-8' }));
        link.href = url;
        link.download = 'rightconnect-kattam-porutham.txt';
        document.body.append(link);
        link.click();
        link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }, 'secondary', 'download'),
      button(t('printReport'), () => window.print(), 'secondary', 'printer'),
      button(t('editBirth'), () => {
        panel.hidden = true;
        state.compatibilityStep = 'kattam';
        renderInput(kattam.inputs);
        focusHeading('#form-title');
      }, 'quiet', 'pencil')
    );
    panel.append(top);
    if (placeNotes.length) {
      const box = text('div', undefined, 'notice');
      placeNotes.forEach(note => box.append(text('p', note)));
      panel.append(box);
    }
    panel.append(report.node, actions);
    icons();
  }
  async function changeReport(action, language, status) {
    const report = state.report;
    if (!report) return;
    await perform(async () => {
      const version = state.reportVersion;
      const result = await request(`/${encodeURIComponent(report.id)}/${action}`, { method: 'POST', token: state.capabilities.get(report.id), body: { language } });
      if (!validReport(result)) throw error('invalidResponse');
      if (version !== state.reportVersion) return;
      acceptReport(result);
    }, status, 'generating');
  }
  async function openReport(id) {
    const status = $('#report-panel .inline-status');
    await perform(async () => {
      const version = state.authVersion;
      const result = await request(`/${encodeURIComponent(id)}`, { token: state.capabilities.get(id) });
      if (version !== state.authVersion) return;
      if (!validReport(result)) throw error('invalidResponse');
      if (!state.report || state.report.id !== result.id) state.inputs = null;
      state.reportVersion += 1;
      setView('services');
      state.selected = descriptorFor(result.service_type) || null;
      acceptReport(result);
    }, status);
  }
  function renderRecovery() {
    const panel = $('#recovery-panel');
    panel.replaceChildren();
    panel.hidden = state.capabilities.size === 0;
    const heading = text('h2', t('recovery'));
    heading.id = 'recovery-title';
    panel.append(heading, text('p', t('recoveryHelp'), 'muted'));
    const list = text('ul', undefined, 'record-list');
    for (const id of Array.from(state.capabilities.keys()).reverse()) {
      const row = text('li', undefined, 'record-row');
      row.append(text('span', `${t('reportId')}: ${id}`));
      const open = button(t('open'), () => openReport(id), 'secondary', 'file-text');
      open.dataset.lock = '';
      row.append(open);
      list.append(row);
    }
    panel.append(list);
    icons();
  }
  function setView(view) {
    state.view = view;
    for (const key of ['services', 'history', 'family']) $(`#${key}-view`).hidden = key !== view;
    document.querySelectorAll('[data-view]').forEach(control => {
      if (control.dataset.view === view) control.setAttribute('aria-current', 'page');
      else control.removeAttribute('aria-current');
    });
  }
  async function showView(view) {
    if (state.busy || (view !== 'services' && !state.session)) return;
    if (state.view === 'services' && state.selected && !$('#input-panel').hidden) state.inputs = readInputs($('#input-panel form'), state.selected);
    captureFamilyDraft();
    notice('');
    setView(view);
    if (view === 'history') await loadHistory();
    if (view === 'family') await loadFamily();
  }
  async function loadHistory() {
    const container = $('#history-content');
    const status = text('p', t('loading'), 'inline-status');
    status.setAttribute('role', 'status');
    container.replaceChildren(status);
    const version = state.authVersion;
    await perform(async () => {
      const data = await request('/history/me', { authenticated: true });
      if (version !== state.authVersion) return;
      if (!Array.isArray(data.reports)) throw error('invalidResponse');
      const list = text('ul', undefined, 'record-list');
      for (const report of data.reports) {
        if (!validReport(report)) continue;
        const descriptor = descriptorFor(report.service_type);
        const row = text('li', undefined, 'record-row');
        const detail = text('div');
        detail.append(text('strong', descriptor ? titleFor(descriptor) : t('reportTitle')), text('small', `${t(report.status)} · ${dateLabel(report.created_at)}`));
        const open = button(t('open'), () => openReport(report.id), 'secondary', 'file-text');
        open.dataset.lock = '';
        row.append(detail, open);
        list.append(row);
      }
      container.replaceChildren(data.reports.length ? list : text('p', t('noHistory'), 'muted'));
    }, status);
    if (container.contains(status)) container.replaceChildren(button(t('reload'), loadHistory, 'secondary', 'refresh-cw'));
  }
  async function fetchMembers() {
    const version = state.authVersion;
    const data = await request('/family/members', { authenticated: true });
    if (version !== state.authVersion) return;
    if (!Array.isArray(data.members)) throw error('invalidResponse');
    state.members = data.members.filter(member => member && typeof member.id === 'string' && typeof member.label === 'string' && member.details);
    state.membersLoaded = true;
  }
  async function loadFamily() {
    const container = $('#family-content');
    const status = text('p', '', 'inline-status');
    status.setAttribute('role', 'status');
    container.replaceChildren(status);
    await perform(async () => {
      await fetchMembers();
      if (state.session) renderFamily();
    }, status);
    if (container.contains(status)) container.replaceChildren(button(t('reload'), loadFamily, 'secondary', 'refresh-cw'));
  }
  function renderFamily() {
    const container = $('#family-content');
    container.replaceChildren();
    if (!state.session) return;
    const add = button(t('addMember'), () => renderMemberEditor(), '', 'user-plus');
    const reload = button(t('reload'), loadFamily, 'secondary', 'refresh-cw');
    add.dataset.lock = '';
    reload.dataset.lock = '';
    const actions = text('div', undefined, 'row-actions');
    actions.append(add, reload);
    container.append(actions);
    const list = text('ul', undefined, 'record-list');
    if (!state.members.length) container.append(text('p', t('emptyFamily'), 'muted'));
    for (const member of state.members) {
      const row = text('li', undefined, 'record-row');
      row.append(text('strong', member.label));
      const actions = text('div', undefined, 'row-actions');
      const edit = button(t('editMember'), () => renderMemberEditor(member), 'secondary', 'pencil');
      const remove = button(t('deleteMember'), () => {
        if (state.busy || !window.confirm(t('deleteConfirm'))) return;
        perform(async () => {
          const version = state.authVersion;
          await request(`/family/members/${encodeURIComponent(member.id)}`, { method: 'DELETE', authenticated: true });
          if (version !== state.authVersion) return;
          state.members = state.members.filter(item => item.id !== member.id);
          refreshSavedPickers();
          state.familyEditor = null;
          renderFamily();
          notice(t('deleted'));
        });
      }, 'danger', 'trash-2');
      edit.dataset.lock = '';
      remove.dataset.lock = '';
      actions.append(edit, remove);
      row.append(actions);
      list.append(row);
    }
    container.append(list);
    if (state.familyEditor) renderMemberEditor(state.familyEditor.member, state.familyEditor.draft);
    icons();
  }
  function renderMemberEditor(member = null, draft = null) {
    if (state.busy && !state.familyEditor) return;
    $('#family-content .family-editor')?.remove();
    state.familyEditor = { member, draft };
    const form = text('form', undefined, 'family-editor');
    form.noValidate = true;
    const heading = text('h3', t(member ? 'editMember' : 'addMember'));
    heading.id = 'member-editor-heading';
    form.append(heading);
    const editable = document.createElement('fieldset');
    editable.dataset.lock = '';
    makeField(editable, { name: 'member-label', label: 'memberLabel', value: draft ? draft.label : member ? member.label : '', maxLength: 100 });
    birthGroup(editable, 'family', 'birth', draft ? draft.details : member ? member.details : {}, false);
    check(editable, 'save-consent', 'saveConsent');
    const actions = text('div', undefined, 'form-actions');
    const save = text('button', t(member ? 'updateMember' : 'saveMember'), 'button');
    save.type = 'submit';
    const cancel = button(t('cancel'), () => { state.familyEditor = null; form.remove(); }, 'quiet', 'x');
    actions.append(save, cancel);
    editable.append(actions);
    const status = text('p', '', 'inline-status');
    status.hidden = true;
    status.setAttribute('role', 'status');
    form.append(editable, status);
    form.addEventListener('submit', event => {
      event.preventDefault();
      if (state.busy || !validateForm(form)) return;
      const payload = { label: form.elements.namedItem('member-label').value.trim(), details: getBirth(form, 'family'), consent: true };
      if (!payload.label) { form.elements.namedItem('member-label').focus(); return; }
      perform(async () => {
        const version = state.authVersion;
        await request(`/family/members${member ? `/${encodeURIComponent(member.id)}` : ''}`, { method: member ? 'PUT' : 'POST', body: payload, authenticated: true });
        if (version !== state.authVersion) return;
        state.familyEditor = null;
        renderFamily();
        notice(t('saved'));
        try {
          await fetchMembers();
          if (version !== state.authVersion) return;
          refreshSavedPickers();
          renderFamily();
        } catch (_) { notice(`${t('saved')} ${t('familyError')}`); }
      }, status);
    });
    $('#family-content').append(form);
    icons();
  }
  function refreshSavedPickers() {
    document.querySelectorAll('#input-panel select[name$="-member"]').forEach(picker => {
      const selected = picker.value;
      picker.replaceChildren();
      for (const [value, label] of [['', t('manualMember')], ...state.members.map(member => [member.id, member.label])]) {
        const option = text('option', label);
        option.value = value;
        picker.append(option);
      }
      picker.value = state.members.some(member => member.id === selected) ? selected : '';
    });
  }
  function captureFamilyDraft() {
    const editor = $('#family-content .family-editor');
    if (editor && state.familyEditor) state.familyEditor.draft = { label: editor.elements.namedItem('member-label').value, details: getBirth(editor, 'family') };
  }
  async function applySession(session) {
    const previousId = state.session && state.session.user.id;
    const nextId = session && session.user.id;
    state.session = session;
    $('#login').hidden = Boolean(session);
    $('#logout').hidden = !session;
    document.querySelectorAll('[data-auth]').forEach(element => { element.hidden = !session; });
    updateLanguageText();
    if (previousId === nextId) return;
    state.authVersion += 1;
    state.reportVersion += 1;
    state.members = [];
    state.membersLoaded = false;
    state.familyEditor = null;
    $('#family-content').replaceChildren();
    $('#history-content').replaceChildren();
    if (previousId) {
      state.inputs = null;
      state.selected = null;
      $('#input-panel').replaceChildren();
      $('#input-panel').hidden = true;
      if (state.report && !state.capabilities.has(state.report.id)) {
        state.report = null;
        $('#report-panel').replaceChildren();
        $('#report-panel').hidden = true;
        $('#catalogue').hidden = false;
      }
      if (!state.report) $('#catalogue').hidden = false;
      setView('services');
    }
    if (state.selected && !$('#input-panel').hidden && !state.busy) {
      captureSelectedInputs();
      rerenderSelectedInput();
    }
    if (session) {
      try { await fetchMembers(); refreshSavedPickers(); }
      catch (failure) {
        if (state.session) {
          notice(t(failure.key === 'onboardingError' ? 'onboardingError' : 'familyError'));
          if (failure.key === 'onboardingError') {
            const registration = text('a', t('completeAccount'), 'registration-link');
            registration.href = '/pages/auth.html';
            $('#global-status').append(' ', registration);
          }
        }
      }
    }
  }
  async function initAuth() {
    try {
      const response = await fetch('/api/v1/auth/provider-config', { cache: 'no-store' });
      if (!response.ok) throw error('loginUnavailable');
      const config = await response.json();
      if (!config.supabase_url || !config.supabase_publishable_key || !window.supabase) throw error('loginUnavailable');
      state.client = window.supabase.createClient(config.supabase_url, config.supabase_publishable_key);
      const { data, error: sessionError } = await state.client.auth.getSession();
      if (sessionError) throw error('loginUnavailable');
      await applySession(data.session);
      state.client.auth.onAuthStateChange((_event, session) => {
        setTimeout(() => { applySession(session).catch(() => notice(t('authError'))); }, 0);
      });
      $('#login').disabled = false;
    } catch (_) { state.client = null; $('#login').disabled = true; }
  }
  async function switchLanguage(next) {
    if (state.busy || next === state.language) return;
    if (state.selected && !$('#input-panel').hidden) captureSelectedInputs();
    captureFamilyDraft();
    state.language = next;
    notice('');
    updateLanguageText();
    renderCatalogue();
    renderRecovery();
    if (state.selected && !$('#input-panel').hidden) rerenderSelectedInput();
    if (state.view === 'family') renderFamily();
    if (state.view === 'history') await loadHistory();
    if (state.kattam && !$('#report-panel').hidden && !state.report) renderKattamReport();
    if (state.report) {
      renderReport();
      if (state.report.status === 'completed' && state.report.language !== next) await changeReport('language', next, $('#report-panel .inline-status'));
    }
  }
  $('#language').addEventListener('change', event => { switchLanguage(event.target.value); });
  $('#reload-services').addEventListener('click', () => perform(loadServices));
  document.querySelectorAll('[data-view]').forEach(control => control.addEventListener('click', () => showView(control.dataset.view)));
  $('#login').addEventListener('click', () => perform(async () => {
    if (!state.client) throw error('loginUnavailable');
    const { error: oauthError } = await state.client.auth.signInWithOAuth({ provider: 'google', options: { redirectTo: `${location.origin}/pages/services.html` } });
    if (oauthError) throw error('loginFailed');
  }));
  $('#logout').addEventListener('click', () => perform(async () => {
    const { error: signOutError } = await state.client.auth.signOut();
    if (signOutError) throw error('authError');
    await applySession(null);
  }));
  // TODO: Add payment integration only when a checkout contract is available.
  // TODO: Add an explicit print-to-PDF action after print output is verified.
  loadCapabilities();
  updateLanguageText();
  renderRecovery();
  loadServices();
  initAuth();
})();