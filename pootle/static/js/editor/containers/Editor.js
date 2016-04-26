/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import EditorTextarea from '../components/EditorTextarea';
import Textarea from '../components/Textarea';
import { getAreaId } from '../utils';


const Editor = React.createClass({

  propTypes: {
    textareaComponent: React.PropTypes.func,
    initialValues: React.PropTypes.array,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
    locale: React.PropTypes.string,
    localeDir: React.PropTypes.string,
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    onChange: React.PropTypes.func.isRequired,
    sourceString: React.PropTypes.string.isRequired,
    style: React.PropTypes.object,
    targetNplurals: React.PropTypes.number.isRequired,
  },

  // FIXME: move context to a higher-order component
  childContextTypes: {
    locale: React.PropTypes.string,
    localeDir: React.PropTypes.string,
  },

  getDefaultProps() {
    return {
      textareaComponent: Textarea,
    };
  },

  getChildContext() {
    return {
      locale: this.props.locale,
      localeDir: this.props.localeDir,
    };
  },

  render() {
    const editorTextareas = [];
    const { values } = this.props;

    for (let i = 0; i < this.props.targetNplurals; i++) {
      const extraProps = {
        isDisabled: this.props.isDisabled,
      };
      if (values !== undefined) {
        extraProps.value = values[i];
        // XXX: hacky way to denote the value was already passed down
        values[i] = null;
      }
      if (this.props.isRawMode !== undefined) {
        extraProps.isRawMode = this.props.isRawMode;
      }
      editorTextareas.push(
        <EditorTextarea
          textareaComponent={this.props.textareaComponent}
          id={getAreaId(i)}
          initialValue={this.props.initialValues[i]}
          key={i}
          onChange={(value) => this.props.onChange(i, value)}
          {...extraProps}
        />
      );
    }
    return (
      <div>
        {editorTextareas}
      </div>
    );
  },

});


export default Editor;