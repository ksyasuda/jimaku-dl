#!/usr/bin/env bash

coverage run -m pytest
coverage html
coverage report -m