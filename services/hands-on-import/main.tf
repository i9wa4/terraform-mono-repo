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
