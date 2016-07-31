/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React from 'react';

import ReactRenderer from 'utils/ReactRenderer';

import Editor from './containers/Editor';


const ReactEditor = {

  init(props) {
    this.node = document.querySelector('.js-mount-editor');
    this.props = {};
    this.hasCRLF = (
      props.hasOwnProperty('sourceString') &&
      props.sourceString.indexOf('\r\n') !== -1
    );

    ReactRenderer.unmountComponents();

    this.setProps(props);
  },

  setProps(props) {
    // Overriding values is a one-time thing: take it into account only if it
    // was passed explicitly.
    const overrideProps = (
      props.hasOwnProperty('overrideValues') ? {} : { overrideValues: null }
    );
    this.props = assign(this.props, props, overrideProps);

    /*           ,
     *  __  _.-"` `'-.
     * /||\'._ __{}_(  CUSTOMS CHECK: we convert potential CRLFs to LFs
     * ||||  |'--.__\  when passing values down to components (`extraProps`),
     * |  L.(   ^_\^   but we keep the original vaues in `this.props`
     * \ .-' |   _ |   just in case the outside world needs to query them.
     * | |   )\___/
     * |  \-'`:._]
     * \__/;      '-.
     */
    const extraProps = {};
    if (this.hasCRLF) {
      if (props.hasOwnProperty('overrideValues')) {
        extraProps.overrideValues = props.overrideValues.map(
          (value) => value.replace(/\r\n/g, '\n')
        );
      }
      if (props.hasOwnProperty('initialValues')) {
        extraProps.initialValues = props.initialValues.map(
          (value) => value.replace(/\r\n/g, '\n')
        );
      }
    }

    this.editorInstance = ReactRenderer.render(
      <Editor
        onChange={this.handleChange}
        {...this.props}
        {...extraProps}
      />,
      this.node
    );
  },

  // FIXME: this additional layer of state tracking is only kept to allow
  // interaction from the outside world. Remove ASAP.
  get stateValues() {
    /*           ,
     *  __  _.-"` `'-.
     * /||\'._ __{}_(  CUSTOMS CHECK: if any CRLF => LF conversion was done
     * ||||  |'--.__\  when passing values down (`this.hasCRLF`), we need to
     * |  L.(   ^_\^   convert values back to their original form (LF => CRLF)
     * \ .-' |   _ |   when providing the hook to the outside world, making
     * | |   )\___/    them unaware of what happened within the component's
     * |  \-'`:._]     ecosystem.
     * \__/;      '-.
     */
    if (this.hasCRLF) {
      return this.editorInstance.state.values.map(
        (value) => value.replace(/\n/g, '\r\n')
      );
    }
    return this.editorInstance.state.values;
  },

  handleChange() {
    PTL.editor.onTextareaChange();
  },

};


export default ReactEditor;
