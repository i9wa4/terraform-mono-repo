# tf-import-test

## 1. terraform import steps

1. Create main.tf.
    ```terraform
    resource "aws_iam_user" "i9wa4" {
    }

    resource "aws_s3_bucket" "i9wa4-minecraft" {
    }
    ```
1. Initialize the project.
    ```terraform
    terraform init
    ```
1. Update terraform.tfstate.
    ```sh
    terraform import aws_iam_user.i9wa4 i9wa4
    terraform import aws_s3_bucket.i9wa4-minecraft i9wa4-minecraft
    ```
1. Make `terraform plan` "No changes." referring terraform.tfstate.
    ```terraform
    resource "aws_iam_user" "i9wa4" {
      name = "i9wa4"
      tags = {
        "test1" = "aaa"
      }
      tags_all = {
        "test1" = "aaa"
      }
    }

    resource "aws_s3_bucket" "i9wa4-minecraft" {
      bucket = "i9wa4-minecraft"
    }
    ```
