#!/usr/bin/env python3

import aws_cdk as cdk

from line_gpt.line_gpt_stack import LineGptStack


app = cdk.App()
LineGptStack(app, "LineGptStack")

app.synth()
