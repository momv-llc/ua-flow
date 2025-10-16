import React from 'react'
import { useTranslation } from 'react-i18next'
import { languages } from '../../i18n'

export default function LanguageSwitch() {
  const { i18n, t } = useTranslation()

  return (
    <label className="language-switcher">
      <span>{t('language.label')}:</span>
      <select value={i18n.language} onChange={(event) => i18n.changeLanguage(event.target.value)}>
        {languages.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label}
          </option>
        ))}
      </select>
    </label>
  )
}

