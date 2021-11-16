total_coverage=$(poetry run pytest | grep "Total coverage")
coverage=$(echo $total_coverage | rev | cut -d' ' -f1 | cut -c 3- | rev)
echo "::set-output name=coverage::${coverage}"
