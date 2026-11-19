/**
 * 登录注册文案 —— Deutsch（L2）。
 *
 * ⚠️ key 集合与 en-US **完全一致**（由 generate.py 保证）。
 *    占位符也必须一致 —— `packages/ui` 的 findPlaceholderMismatches() 会校验。
 */

export const deDE = {
  'identity.title.signIn': 'Anmelden',
  'identity.title.signUp': 'Registrieren',
  'identity.subtitle.signIn':
    'Melden Sie sich an, um Ihren akademischen Arbeitsbereich weiter zu nutzen',
  'identity.subtitle.signUp': 'Erstellen Sie ein Konto für Ihre akademische Reise',
  'identity.tab.signIn': 'Anmelden',
  'identity.tab.signUp': 'Registrieren',
  'identity.field.email': 'E-Mail',
  'identity.field.emailPlaceholder': 'name@example.com',
  'identity.field.password': 'Passwort',
  'identity.field.passwordPlaceholder': 'Mindestens 10 Zeichen, mit Ziffer und Buchstabe',
  'identity.field.phone': 'Telefonnummer',
  'identity.field.phonePlaceholder': '13800138000',
  'identity.field.code': 'Bestätigungscode',
  'identity.field.codePlaceholder': '6 Ziffern',
  'identity.field.displayName': 'Anzeigename',
  'identity.field.displayNamePlaceholder': 'Optional',
  'identity.action.signIn': 'Anmelden',
  'identity.action.signUp': 'Registrieren',
  'identity.action.sendCode': 'Code senden',
  'identity.action.resendCode': 'Erneut senden ({seconds} Sek.)',
  'identity.action.wechat': 'Mit WeChat anmelden',
  'identity.action.google': 'Mit Google anmelden',
  'identity.action.github': 'Mit GitHub anmelden',
  'identity.action.switchToSignUp': 'Kein Konto? Registrieren',
  'identity.action.switchToSignIn': 'Schon ein Konto? Anmelden',
  'identity.action.back': 'Zurück',
  'identity.divider.or': 'oder',
  'identity.state.sending': 'Wird gesendet…',
  'identity.state.verifying': 'Wird geprüft…',
  'identity.state.redirecting': 'Weiterleitung…',
  'identity.error.emailRequired': 'E-Mail ist erforderlich',
  'identity.error.emailInvalid': 'Ungültige E-Mail-Adresse',
  'identity.error.emailTaken': 'Diese E-Mail-Adresse ist bereits registriert',
  'identity.error.passwordRequired': 'Passwort ist erforderlich',
  'identity.error.passwordTooShort': 'Das Passwort muss mindestens 10 Zeichen lang sein',
  'identity.error.passwordNeedsNumber': 'Das Passwort muss eine Ziffer enthalten',
  'identity.error.passwordNeedsLetter': 'Das Passwort muss einen Buchstaben enthalten',
  'identity.error.phoneRequired': 'Telefonnummer ist erforderlich',
  'identity.error.phoneInvalid': 'Ungültige Telefonnummer',
  'identity.error.codeRequired': 'Bestätigungscode ist erforderlich',
  'identity.error.codeInvalid': 'Bestätigungscode ungültig oder abgelaufen',
  'identity.error.credentialsInvalid': 'E-Mail oder Passwort ist falsch',
  'identity.error.accountSuspended':
    'Dieses Konto ist gesperrt. Bitte wenden Sie sich an eine Administration.',
  'identity.error.network':
    'Netzwerkfehler. Prüfen Sie Ihre Verbindung und versuchen Sie es erneut.',
  'identity.error.unknown': 'Ein unbekannter Fehler ist aufgetreten',
  'identity.hint.emailRequired': 'Wir müssen Ihre E-Mail-Adresse verifizieren',
  'identity.hint.emailRequiredDescription':
    'Ihre E-Mail-Adresse wird für Bestätigungsmails und zur Wiederherstellung des Passworts genutzt. Einige Anmeldearten (etwa WeChat) liefern keine E-Mail-Adresse — dann müssen Sie sie manuell ergänzen.',
  'identity.hint.codeSent': 'Bestätigungscode an {email} gesendet',
  'identity.hint.agreeToTerms':
    'Mit der Registrierung stimmen Sie den Nutzungsbedingungen und der Datenschutzerklärung zu',
} as const;
