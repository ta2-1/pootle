.. _user_score:

Similarity ratio
================

We calculate a user score to evaluate real amount of work that was
done for translating or reviewing each unit. The similarity ratio
concept is leveraged for that.

*Similarity ratio* is the real number in ``[0..1]`` range that shows how
different is the submitted translation from the next most similar one.
``0`` means the string is totally different from anything else, ``1`` means
that the translation is identical to the one we already know about::

    S(Str_new, Str_old) = (
        1 - levenshtein_words(Str_new, Str_old) /
        max(length_words(Str_new), length_words(Str_old)))
where

``levenshtein_words(Str_new, Str_old)`` is the number of edits (in words)
calculated using Levenshtein algorithm which is needed to transform
``Str_old`` into ``Str_new``.

In terms of similarity calculation, words are just chunks of text
split by one or more whitespace symbols.

We will be storing two different similarity value calculations with
each submission and suggestion:

* *similarity* — similarity ratio based on translations gathered from
  suggestionsand from similar translationsresults this is calculated
  based on all suggestions and similar translations visible to the
  translator in the editor at the moment he submits a translation.
* *mt_similarity* — similarity ratio based on comparison with the
  machine-provided translation (e.g. Google Translate) this is calculated
  only if the user has used the pre-translate function on a unit prior
  to submitting it.

When the user translates a new unit, we store both types of
similarity, but use ``S = max(similarity, mt_similarity)`` for any further
calculations.

There are two major translators activities: 1) translation and 2) reviewing.

We agree on that raw translation is ``5/7`` of the price,
whereas reviewing is ``2/7`` (in terms of labor and in terms of money).

