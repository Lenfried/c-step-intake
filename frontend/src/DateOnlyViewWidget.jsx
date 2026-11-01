/**
 * View widget for date-only fields, such as date of birth, that shows the
 * day as entered in any time zone. See dateOnly.js.
 */
import React from 'react';
import { useSelector } from 'react-redux';
import { toBackendLang } from '@plone/volto/helpers/Utils/Utils';
import { formatDateOnly } from './dateOnly';

const DateOnlyViewWidget = ({ value }) => {
  const lang = useSelector((state) => state.intl.locale);
  return value ? (
    <span className="date widget">
      {formatDateOnly(value, toBackendLang(lang))}
    </span>
  ) : (
    ''
  );
};

export default DateOnlyViewWidget;
