/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';

import {
  applyFontFilter, unapplyFontFilter, isNewlineSymbol, countNewlineCharacter,
  countNewlineSymbol, removeNewlineChar, convertNewlineSymbolToChar,
} from '../utils';


function shouldEventOverwriteSelection(e) {
  const { key } = e;
  return (
    !e.getModifierState(key) &&
    !e.altKey && !e.ctrlKey && !e.shiftKey && !e.metaKey &&
    key !== 'Tab' &&
    key.search(/^Arrow[a-zA-Z]+$/) === -1 &&
    key.search(/^F[0-9]{1,2}$/) === -1
  );
}


const EditorTextarea = React.createClass({

  propTypes: {
    textareaComponent: React.PropTypes.func,
    id: React.PropTypes.string,
    initialValue: React.PropTypes.string,
    isDisabled: React.PropTypes.bool,
    isRawMode: React.PropTypes.bool,
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    onChange: React.PropTypes.func.isRequired,
    value: React.PropTypes.string,
    style: React.PropTypes.object,
  },

  getDefaultProps() {
    return {
      initialValue: '',
    };
  },

  getInitialState() {
    return {
      value: this.props.initialValue,
    };
  },

  componentWillReceiveProps(nextProps) {
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    if (nextProps.value && nextProps.value !== null) {
      this.updateValue(nextProps.value);
    }
  },

  getMode() {
    return this.props.isRawMode ? 'raw' : 'regular';
  },

  updateValue(newValue) {
    // FIXME: needed to allow interaction from the outside world. Remove ASAP.
    this.props.onChange(newValue);

    this.setState({
      value: newValue,
    });
  },

  handleChange(e) {
    const newValue = e.target.value;
    const cleanValue = unapplyFontFilter(newValue, this.getMode());
    this.updateValue(cleanValue);
  },

  handleKeyDown(e) {
    const { selectionStart } = e.target;
    const { selectionEnd } = e.target;
    const { value } = e.target;

    if (selectionStart === selectionEnd) {
      if (e.key === 'Backspace' && isNewlineSymbol(value[selectionStart - 1])) {
        e.preventDefault();
        this.updateValueWithSelection(value, selectionStart, selectionEnd + 1, e.key);
      } else if (e.key === 'Delete' && isNewlineSymbol(value[selectionEnd])) {
        e.preventDefault();
        this.updateValueWithSelection(value, selectionStart + 1, selectionEnd + 2, e.key);
      }
    } else {
      const start = Math.min(selectionStart, selectionEnd);
      const end = Math.max(selectionStart, selectionEnd);

      if (shouldEventOverwriteSelection(e) && isNewlineSymbol(value[end - 1])) {
        e.preventDefault();
        this.updateValueWithSelection(value, start, end + 1, e.key);
      }
    }
  },

  updateValueWithSelection(value, start, end, keyPressed) {
    const replacementChar = (
      (keyPressed === 'Delete' || keyPressed === 'Backspace') ? '' : keyPressed
    );
    const newValue = (value.slice(0, start) + replacementChar +
                      value.slice(end, value.length));
    const cleanValue = unapplyFontFilter(newValue, this.getMode());
    this.updateValue(cleanValue);
  },

  handleCopyCut(e) {
    const { selectionStart } = e.target;
    const { selectionEnd } = e.target;
    const { value } = e.target;
    let selectedValue = value.slice(selectionStart, selectionEnd);

    // Special-case: the selected text contains more newline symbols than
    // actual newline characters
    if (countNewlineSymbol(selectedValue) > countNewlineCharacter(selectedValue)) {
      // 1. Remove actual newline characters
      selectedValue = removeNewlineChar(selectedValue);
      // 2. Convert symbols into actual characters
      selectedValue = convertNewlineSymbolToChar(selectedValue);
    }

    const valueToClipboard = unapplyFontFilter(selectedValue, this.getMode());
    e.clipboardData.setData('text/plain', valueToClipboard);

    e.preventDefault();
    if (e.type === 'cut') {
      const end = isNewlineSymbol(value[selectionEnd - 1])
        ? selectionEnd + 1
        : selectionEnd;
      this.updateValueWithSelection(value, selectionStart, end, 'Delete');
    }
  },

  render() {
    const transformedValue = applyFontFilter(this.state.value, this.getMode());
    const editorWrapperClasses = cx('editor-area-wrapper js-editor-area-wrapper', {
      'is-disabled': this.props.isDisabled,
    });

    return (
      <div className={editorWrapperClasses}>
        <this.props.textareaComponent
          id={this.props.id}
          initialValue={applyFontFilter(this.props.initialValue, this.getMode())}
          onChange={this.handleChange}
          onCopy={this.handleCopyCut}
          onCut={this.handleCopyCut}
          onKeyDown={this.handleKeyDown}
          style={this.props.style}
          value={transformedValue}
        />
      </div>
    );
  },

});


export default EditorTextarea;
