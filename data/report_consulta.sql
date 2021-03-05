-- Relatório Atestados
SELECT CASE
  WHEN vinculo = 'Magistrado' THEN '3 - Exames Periódicos - Magistrados'
  ELSE '4 - Exames Periódicos - Servidores'
  END as tipo_info,
  cid_codigo,
  '' as desc,
  CASE WHEN sexo1 = 'M' THEN '1 - Masculino'
        WHEN sexo1 = 'F' THEN '2 - Feminino' END,
  CASE
    WHEN faixa = '35 menor' THEN '1 - Menor do que 35 anos de idade'
    WHEN faixa = '36 a 45' THEN '2 - De 36 a 45 anos de idade'
    WHEN faixa = '46 a 55' THEN '3 - De 46 a 55 anos de idade'
    WHEN faixa = '56 a 65' THEN '4 - De 56 a 65 anos de idade'
    WHEN faixa = '66 maior'  THEN '5 - Maior do que 66 anos de idade'
END,
    CASE
      WHEN vinculo = 'Magistrado' AND grau = '1' THEN '1 - Se Magistrado - Atua no 1o Grau de Jurisdição'
       WHEN vinculo = 'Magistrado' AND grau = '2' THEN '2 - Se Magistrado - Atua no 2o Grau de Jurisdição'
       WHEN vinculo = 'Servidor' AND grau = '1'  AND area = 'Judiciária' THEN '4 - Se Servidor - Atua na Área Judiciária no 1o Grau de Jurisdição'
       WHEN vinculo = 'Servidor' AND grau = '1'  AND area = 'Administrativa' THEN '5 - Se Servidor - Atua na Área Administrativa no 1o Grau de Jurisdição'
       WHEN vinculo = 'Servidor' AND grau = '2'  AND area = 'Judiciária' THEN '6 - Se Servidor - Atua na Área Judiciária no 2o Grau de Jurisdição'
       ELSE '7 - Se Servidor - Atua na Área Administrativa no 2o Grau de Jurisdição'
  END as sub_class,
  frequencia

FROM
 (SELECT
  CASE
  WHEN extract(YEAR FROM age(TIMESTAMP '2018-12-31', partner.birthday)) < 36
    THEN '35 menor'
  WHEN extract(YEAR FROM age(TIMESTAMP '2018-12-31', partner.birthday)) BETWEEN 36 AND 45
    THEN '36 a 45'
  WHEN extract(YEAR FROM age(TIMESTAMP '2018-12-31', partner.birthday)) BETWEEN 46 AND 55
    THEN '46 a 55'
  WHEN extract(YEAR FROM age(TIMESTAMP '2018-12-31', partner.birthday)) BETWEEN 56 AND 65
    THEN '56 a 65'
  WHEN extract(YEAR FROM age(TIMESTAMP '2018-12-31', partner.birthday)) >= 66
    THEN '66 maior' END                             AS faixa,
  categoria.codigo                                  AS cid_codigo,
  CASE
  WHEN partner.title = 3
    THEN 'M'
  WHEN partner.title = 1 OR partner.title = 2
    THEN 'F' END                                    AS sexo1,
  COUNT(consulta.id)                                AS frequencia,
  CASE WHEN partner.function = 'Magistrado'
    THEN 'Magistrado'
  WHEN partner.function = 'Servidor Carreira' OR
       partner.function = 'Cargo Comissionado' THEN 'Servidor' END as vinculo,
  tv.grau as grau,
  CASE WHEN tv.area = 'meio'
    THEN 'Administrativa'
  WHEN tv.area = 'fim'
    THEN 'Judiciária' END as area
FROM saude_atendimento_consulta AS consulta
  JOIN saude_atendimento_consulta_saude_cid_subcategoria_rel ON consulta.id = saude_atendimento_consulta_saude_cid_subcategoria_rel.saude_atendimento_consulta_id
  JOIN saude_cid_subcategoria AS subcategoria ON subcategoria.id = saude_cid_subcategoria_id
  JOIN saude_cid_categoria AS categoria ON subcategoria.categoria_id = categoria.id
  JOIN saude_paciente AS paciente ON paciente.id = consulta.paciente_id
  JOIN res_partner AS partner ON partner.id = paciente.partner_id
  JOIN tjpi_vinculo tv ON partner.id = tv.partner_id
WHERE date_part('year', consulta.create_date) :: BIGINT = 2018 AND partner.is_company = FALSE AND consulta.atestado = FALSE AND
      partner.function IN ('Magistrado', 'Servidor Carreira', 'Cargo Comissionado') and tv.area is not NULL
GROUP BY
  faixa, cid_codigo, sexo1, tv.grau, vinculo,
  tv.area
ORDER BY faixa, vinculo, cid_codigo) as P