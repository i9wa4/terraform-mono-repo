variable "sfn_role_arn" {
  type = string
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1"
}

resource "aws_sfn_state_machine" "sfn_state_machine" {
  name     = "MyStateMachine-1opxzs145"
  role_arn = var.sfn_role_arn
  definition = jsonencode(
    {
      StartAt = "HasName"
      States = {
        FillName = {
          Next       = "Say"
          Result     = "World"
          ResultPath = "$.name"
          Type       = "Pass"
        }
        HasName = {
          Choices = [
            {
              IsPresent = false
              Next      = "FillName"
              Variable  = "$.name"
            },
          ]
          Default = "Say"
          Type    = "Choice"
        }
        Say = {
          Next = "Say2"
          Parameters = {
            "message.$" = "States.Format('Hello, {}', $.name)"
            "namex.$"   = "$.name"
          }
          Type = "Pass"
        }
        Say2 = {
          Next = "SayLast"
          Parameters = {
            "say2.$"    = "$.namex"
            "name.$"    = "$.namex"
            "message.$" = "$.message"
          }
          Type = "Pass"
        }
        SayLast = {
          End        = true
          OutputPath = "$.message"
          Type       = "Pass"
        }
      }
    }
  )
}
