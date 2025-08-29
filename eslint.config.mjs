import eslint from '@eslint/js';
import tsEslint from 'typescript-eslint';
import stylistic from '@stylistic/eslint-plugin';

import { globalIgnores } from 'eslint/config';

import globals from 'globals';

export default tsEslint.config(
    globalIgnores([
        '**/dist',
        '**/lib',
        '**/node_modules',
    ]),

    {
        extends: [eslint.configs.recommended],

        rules: {
            'no-unused-vars': 'off',
        },
    },
    {
        extends: [tsEslint.configs.recommended],

        files: ['**/*.ts', '**/*.tsx', '**/*.js', '**/*.jsx', '**/*.mjs'],

        rules: {
            '@typescript-eslint/no-explicit-any':   'off',
            '@typescript-eslint/no-empty-function': 'off',

            '@typescript-eslint/no-unused-vars': [
                'warn',
                {
                    varsIgnorePattern:         '^_',
                    caughtErrorsIgnorePattern: '^_',
                    argsIgnorePattern:         '^_',
                },
            ],

        },
    },
    {
        extends: [tsEslint.configs.stylistic],

        rules: {
            '@typescript-eslint/consistent-type-definitions': 'off',
        },
    },
    {
        extends: [stylistic.configs.recommended],

        languageOptions: {
            globals: {
                ...globals.browser,
            },
        },

        rules: {
            '@stylistic/arrow-parens': ['warn', 'as-needed'],
            '@stylistic/semi':         ['warn', 'always'],

            '@stylistic/brace-style': ['warn', '1tbs', {
                allowSingleLine: true,
            }],

            '@stylistic/indent': ['warn', 4, {
                SwitchCase: 0,
            }],

            '@stylistic/key-spacing': ['warn', {
                beforeColon: false,
                afterColon:  true,
                align:       'value',
            }],

            '@stylistic/max-statements-per-line': ['error', {
                max: 2,
            }],

            '@stylistic/member-delimiter-style': ['warn', {
                multiline: {
                    delimiter:   'semi',
                    requireLast: true,
                },

                singleline: {
                    delimiter:   'comma',
                    requireLast: false,
                },

                multilineDetection: 'brackets',
            }],

            '@stylistic/no-multi-spaces': ['warn', {
                exceptions: {
                    Property:         true,
                    ImportAttribute:  true,
                    TSTypeAnnotation: true,
                },
            }],

            '@stylistic/quotes': ['warn', 'single', {
                allowTemplateLiterals: 'never',
            }],
        },
    },
);
