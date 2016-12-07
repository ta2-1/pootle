/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import UnitPluralFormLabel from './UnitPluralFormLabel';

const EditorPluralFormHeader = React.createClass({
  propTypes: {
    targetNplurals: React.PropTypes.number.isRequired,
    index: React.PropTypes.number.isRequired,
  },

  render() {
    if (this.props.targetNplurals === 1) {
      return null;
    }
    return (
      <div className="subheader">
        <UnitPluralFormLabel
          value={`${this.props.index}`}
          className="title"
        />
      </div>
    );
  },
});


export default EditorPluralFormHeader;
