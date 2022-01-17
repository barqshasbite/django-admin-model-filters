(function($) {
	'use strict';

	/**
	 * Handle the field select input changing.
	 *
	 * If the special "OR" field is selected, disable the inputs in the entire
	 * row so that they cannot be changed on the UI.
	 *
	 * @param field Field that has changed.
	 */
	function fieldChanged(field) {
		let root = $(document.body);
		let fieldPrefix = field.attr('id').split("-").slice(0, 2).join("-");
		let operator = root.find("#" + fieldPrefix + "-operator");
		let value = root.find("#" + fieldPrefix + "-value");
		let negate = root.find("#" + fieldPrefix + "-negate");
		if (field.val() === "__OR__") {
			operator.val("exact");
			operator.prop("disabled", true);
			operator.after($('<input>', {
				type: 'hidden',
				name: operator.attr("name"),
				value: operator.val()
			}));
			value.val("");
			value.prop("disabled", true);
			value.after($('<input>', {
				type: 'hidden',
				name: value.attr("name"),
				value: value.val()
			}));
			negate.val(false);
			negate.prop("disabled", true);
		} else {
			operator.prop("disabled", false);
			operator.siblings('input[type="hidden"]').remove();
			value.prop("disabled", false);
			value.siblings('input[type="hidden"]').remove();
			negate.prop("disabled", false);
			updateOperators(operator, field);
			updateChoices(value, field);
		}
	}

	/**
	 * Update the operator select input based on the field.
	 *
	 * @param operator The operator select input.
	 * @param field The field to update operators with.
	 */
	function updateOperators(operator, field) {
		let operatorValue = operator.val();
		let operatorExists = false;
		let operators = _MF_OPERATOR_MAP[field.val()];
		operator.empty();
		operators.forEach(function(operatorData) {
			$(operator).append($('<option>', {
				text: operatorData.display,
				value: operatorData.key
			}));
			if(operatorValue === operatorData.key) {
				operatorExists = true;
			}
		});
		if(operatorExists) {
			operator.val(operatorValue);
		} else {
			operator.val(operators[0].key);
		}
	}

	/**
	 * Update the value input based on the field.
	 *
	 * If the field has a designated list of choices that can be used, then
	 * replace the input with a select input and populate it with only the
	 * available choices.
	 *
	 * If the field does not have a designated list of choices, then use a
	 * simple input text box to allow any input.
	 *
	 * @param value The value input.
	 * @param field The field to update value with.
	 */
	function updateChoices(value, field) {
		let fieldValue = value.val();
		let valueExists = false;
		let choices = _MF_VALUE_MAP[field.val()];
		if(choices && choices.length > 0) {
			let select = $('<select>', {
				id: value.attr("id"),
				name: value.attr("name"),
				class: value.attr("class")
			});
			choices.forEach(function(choice) {
				$(select).append($('<option>', {
					text: choice.display,
					value: choice.key
				}));
				if(fieldValue.toString() === choice.key.toString()) {
					valueExists = true;
				}
			});
			if(valueExists) {
				select.val(fieldValue);
			} else {
				select.val(choices[0].key);
			}
			value.replaceWith(select);
		} else if (value.is("select")) {
			let input = $('<input>', {
				id: value.attr("id"),
				name: value.attr("name"),
				type: "text",
				class: value.attr("class"),
			});
			input.val(fieldValue);
			value.replaceWith(input);
		}
	}

	/**
	 * Add change listeners to field select inputs.
	 */
	function addChangeListeners() {
		$('select.af-query-field').each(function() {
			$(this).on("change", function() {
				fieldChanged($(this));
			});
			fieldChanged($(this));
		});
	}

	/**
	 * Remove change listeners from field select inputs.
	 */
	function removeChangeListeners() {
		$('select.af-query-field').each(function() {
			$(this).off("change");
		});
	}

	/**
	 * Monitor for new inline fields being added.
	 *
	 * When a new inline is added, the change listeners are refreshed.
	 *
	 * @returns {MutationObserver}
	 */
	function buildMutationObserver() {
		return new MutationObserver(function(mutations) {
			mutations.forEach(function(mutation) {
				if (mutation.addedNodes && mutation.addedNodes.length > 0) {
					for (let elem of mutation.addedNodes) {
						if ($(mutation.target).find('.af-query-field').length) {
							removeChangeListeners();
							addChangeListeners();
							break;
						}
					}
				}
			});
		});
	}

	/**
	 * Initialize the model filters javascript.
	 */
	function init() {
		addChangeListeners();
		let observer = buildMutationObserver();
		let observerConfig = {childList: true, subtree: true};
		observer.observe(document.body, observerConfig);
	}

	$(document).ready(init);

})(jQuery || django.jQuery);
