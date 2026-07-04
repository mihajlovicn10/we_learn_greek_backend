# Generated manually for demo fix

from django.conf import settings
from django.db import migrations, models
import dictionary.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dictionary', '0004_alter_dictionary_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dictionary',
            name='greek_word',
            field=models.CharField(
                help_text='Enter the word in Greek (only Greek Alphabet allowed, optionally with an article).',
                max_length=30,
                validators=[dictionary.validators.validate_greek],
            ),
        ),
        migrations.AlterUniqueTogether(
            name='dictionary',
            unique_together={('user', 'greek_word')},
        ),
    ]
